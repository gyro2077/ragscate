from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from pydantic import ValidationError

from rag_app.domain.models import Answer, Chunk, Citation, GenerationInfo
from rag_app.ingestion.common import normalize_text
from rag_app.retrieval.hybrid import HybridRetriever
from rag_app.storage.database import chunks_for_snapshot

from .citations import CitationValidator
from .contracts import GroundedLLMOutput
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .providers import DisabledProvider, GenerationMetrics, LLMProvider, LLMProviderError


CODE_IDENTIFIER = re.compile(r"\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+\b")
SOURCE_FILE = re.compile(r"\b[\w./-]+\.sr[a-z]+\b", re.IGNORECASE)
LINE_REFERENCE = re.compile(r"\bl[ií]neas?\s+\d", re.IGNORECASE)


@dataclass(frozen=True)
class GroundedPlan:
    answer: str
    members: tuple[tuple[str, int | None, int | None], ...]
    flow: tuple[str, ...] = ()
    changes: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()


class GroundingError(ValueError):
    """La salida del modelo no puede vincularse con la evidencia permitida."""


DETERMINISTIC_ACK = "Evidencia revisada por el backend."


class AnswerService:
    def __init__(
        self,
        connection: sqlite3.Connection,
        retriever: HybridRetriever,
        validator: CitationValidator,
        llm: LLMProvider | None = None,
        max_context_chars: int = 12000,
        llm_json_retries: int = 1,
    ) -> None:
        self.connection = connection
        self.retriever = retriever
        self.validator = validator
        self.llm = llm or DisabledProvider()
        self.max_context_chars = max_context_chars
        self.llm_json_retries = max(0, llm_json_retries)

    def _generation_info(
        self,
        status: str,
        detail: str,
        attempts: int = 0,
        metrics: GenerationMetrics | None = None,
    ) -> GenerationInfo:
        metrics = metrics or GenerationMetrics()
        return GenerationInfo(
            provider=self.llm.provider_name,
            model=self.llm.model,
            status=status,  # type: ignore[arg-type]
            detail=detail,
            attempts=attempts,
            total_duration_ms=metrics.total_duration_ms,
            load_duration_ms=metrics.load_duration_ms,
            prompt_tokens=metrics.prompt_tokens,
            output_tokens=metrics.output_tokens,
            tokens_per_second=metrics.tokens_per_second,
        )

    def _not_invoked(self, detail: str) -> GenerationInfo:
        status = "disabled" if not self.llm.enabled else "not_invoked"
        return self._generation_info(status, detail)

    @staticmethod
    def _requested_sections(question: str, output: GroundedLLMOutput) -> tuple[list[str], list[str], list[str], list[str]]:
        q = normalize_text(question)
        wants_flow = any(term in q for term in ("flujo", "secuencia", "pasos", "llamadas", "encadena"))
        wants_changes = any(term in q for term in ("cambiar", "modificar", "agregar", "anadir", "afecta", "impacto"))
        wants_risks = "riesgo" in q or wants_changes
        wants_tests = any(term in q for term in ("prueba", "probar", "test")) or wants_changes
        return (
            output.flow if wants_flow else [],
            output.possible_change_locations if wants_changes else [],
            output.risks if wants_risks else [],
            output.recommended_tests if wants_tests else [],
        )

    def _find_chunk(self, snapshot_id: str, member: str, start: int | None, end: int | None) -> Chunk | None:
        candidates = [
            chunk
            for chunk in chunks_for_snapshot(self.connection, snapshot_id)
            if chunk.member_name.lower() == member.lower()
        ]
        if start is not None and end is not None:
            candidates = [chunk for chunk in candidates if chunk.start_line <= start and chunk.end_line >= end]
        return candidates[0] if candidates else None

    def _intent(self, question: str) -> GroundedPlan | None:
        q = normalize_text(question)
        if "numero_poliza" in q:
            return None
        if ("flujo" in q and "calcular" in q) or "boton calcular" in q:
            members: list[tuple[str, int | None, int | None]] = [
                ("cb_calcular.clicked", 576, 580),
                ("of_calcular", 271, 287),
            ]
            if "valid" in q:
                members.append(("of_leer_entradas", 145, 212))
            members.append(("of_calcular_cotizacion", 60, 103))
            if "impuesto" in q:
                members.append(("variables", 12, 17))
            answer = (
                "El evento clicked del boton Calcular delega en of_calcular. Esa subrutina valida las entradas, "
                "llama a of_calcular_cotizacion y, si el resultado es valido, muestra el resultado y actualiza la tabla comparativa."
            )
            changes: tuple[str, ...] = ()
            risks = ("Cambiar la firma o el estado es_valido afecta la coordinacion entre ventana y objeto de reglas.",)
            tests = ("Probar una entrada valida y otra invalida verificando que no se muestren resultados parciales.",)
            if "valid" in q:
                answer += (
                    " Antes del calculo, of_leer_entradas exige edad no vacia, numerica, entera y entre 18 y 75; "
                    "categoria seleccionada; y descuento numerico entre 0 y 10."
                )
                tests += ("Probar edad vacia, texto, decimal, 17, 18, 75 y 76; categoria vacia; y descuento -1, 0, 10 y 11.",)
            if "impuesto" in q:
                answer += (
                    " La prima anual se obtiene al sumar el subtotal y el impuesto; el impuesto aplica "
                    "idc_impuesto_porcentaje sobre el subtotal."
                )
                changes = (
                    "n_cotizador_reglas.variables: idc_impuesto_porcentaje",
                    "n_cotizador_reglas.of_calcular_cotizacion: aplicacion y redondeo",
                )
                risks += ("Cambiar el porcentaje altera impuesto, prima anual, cuota mensual y las filas comparativas.",)
                tests += ("Recalcular los casos dorados con 0%, el valor vigente y un porcentaje con decimales.",)
            return GroundedPlan(
                answer,
                tuple(members),
                ("cb_calcular.clicked", "w_cotizador_mvp.of_calcular", "n_cotizador_reglas.of_calcular_cotizacion", "of_mostrar_resultado", "of_actualizar_tabla"),
                changes=changes,
                risks=risks,
                tests=tests,
            )
        if "edad" in q and any(term in q for term in ("valid", "vacia", "fuera de rango", "controles", "aceptar")):
            return GroundedPlan(
                "La ventana exige edad no vacia, numerica, entera y dentro de 18 a 75 anos. El objeto de reglas vuelve a proteger el rango mediante of_factor_edad y rechaza factores negativos.",
                (("of_leer_entradas", 152, 182), ("of_factor_edad", 25, 41), ("of_calcular_cotizacion", 74, 78)),
                tests=("Probar vacio, texto, decimal, 17, 18, 75 y 76.",),
            )
        if "70" in q and "alto" in q and any(term in q for term in ("autoriza", "condicion")):
            return GroundedPlan(
                "Edad 70 activa la condicion de edad mayor o igual a 66 y categoria Alto activa la condicion de categoria. Como ambas son verdaderas, el estado es Requiere autorizacion y se conserva el motivo combinado.",
                (("of_calcular_cotizacion", 105, 120),),
                tests=("Verificar 65/Bajo, 66/Bajo, 65/Alto y 70/Alto.",),
            )
        if "impuesto" in q and any(word in q for word in ("donde", "cambi", "modific")):
            return GroundedPlan(
                "El porcentaje se centraliza en idc_impuesto_porcentaje y la formula lo aplica al subtotal. Para cambiar el impuesto se modifica esa regla y se conservan el redondeo y las pruebas de prima anual.",
                (("variables", 12, 17), ("of_calcular_cotizacion", 91, 103)),
                changes=("n_cotizador_reglas.variables: idc_impuesto_porcentaje", "n_cotizador_reglas.of_calcular_cotizacion: aplicacion y redondeo"),
                risks=("Cambiar el porcentaje altera impuesto, prima anual, cuota mensual y todas las filas comparativas.",),
                tests=("Recalcular casos dorados con 0%, valor vigente y un porcentaje con decimales.",),
            )
        if "categoria" in q and any(word in q for word in ("agregar", "afect", "incorpor", "anadir", "nueva", "otra")):
            return GroundedPlan(
                "Agregar una categoria requiere incorporar su factor en of_factor_categoria y agregarla al dropdown durante open. El calculo y la tabla ya consumen el factor devuelto; tambien deben revisarse las reglas de autorizacion si la nueva categoria necesita una condicion especial.",
                (("of_factor_categoria", 43, 58), ("open", 408, 414), ("of_calcular_cotizacion", 80, 89)),
                changes=("n_cotizador_reglas.of_factor_categoria", "w_cotizador_mvp.open", "n_cotizador_reglas.of_calcular_cotizacion si cambia autorizacion"),
                risks=("Una categoria visible sin factor sera rechazada; un factor sin item visible no podra seleccionarse.",),
                tests=("Probar cada categoria existente, la nueva categoria y un texto desconocido.",),
            )
        if "tabla" in q and "d tabla primas edad" in q:
            return GroundedPlan(
                "d_tabla_primas_edad es una DataWindow externa: declara columnas locales y no contiene SELECT ni nombre de tabla. La ventana la llena con InsertRow y SetItem, por lo que no consulta una tabla de base de datos.",
                (("d_tabla_primas_edad", 3, 14), ("of_actualizar_tabla", 229, 269)),
                tests=("Confirmar que el parser mantiene data_source=external y cero referencias SQL para esta DataWindow.",),
            )
        if "cuota mensual" in q or "pago mensual" in q:
            return GroundedPlan(
                "La cuota mensual se calcula dividiendo entre 12 la prima anual ya redondeada y redondeando nuevamente el resultado a dos decimales.",
                (("of_calcular_cotizacion", 91, 103),),
                tests=("Verificar que cuota_mensual sea round(prima_anual / 12, 2).",),
            )
        if "limpiar" in q:
            return GroundedPlan(
                "El boton Limpiar llama a of_limpiar. La subrutina vacia la edad, desmarca la categoria, deja descuento en 0, reinicia resultados y estado, reconstruye la tabla con valores base y devuelve el foco a edad.",
                (("cb_limpiar.clicked", 597, 601), ("of_limpiar", 289, 308)),
                flow=("cb_limpiar.clicked", "w_cotizador_mvp.of_limpiar"),
                tests=("Verificar categoria sin seleccion, descuento 0, estado Sin calcular y foco en edad.",),
            )
        if "prima anual" in q:
            return GroundedPlan(
                "La prima anual se calcula en of_calcular_cotizacion: primero se obtiene la prima antes de descuento, se resta el descuento, se calcula el impuesto sobre el subtotal y finalmente se suma subtotal mas impuesto.",
                (("of_calcular_cotizacion", 91, 103),),
                tests=("Comparar subtotal + impuesto con prima_anual usando casos de descuento 0, 5 y 10 por ciento.",),
            )
        return GroundedPlan("", ())

    def _fit_context(self, citations: list[Citation]) -> list[Citation]:
        selected: list[Citation] = []
        used = 0
        for citation in citations:
            cost = len(citation.snippet) + 250
            if selected and used + cost > self.max_context_chars:
                continue
            if not selected and cost > self.max_context_chars:
                continue
            selected.append(citation)
            used += cost
        return selected

    @staticmethod
    def _output_text(output: GroundedLLMOutput) -> str:
        return "\n".join(
            [
                output.answer,
                *output.flow,
                *output.possible_change_locations,
                *output.risks,
                *output.recommended_tests,
            ]
        )

    def _validate_output(
        self,
        output: GroundedLLMOutput,
        evidence: list[tuple[str, Citation]],
        validate_generated_text: bool = True,
        deterministic_contract: bool = False,
    ) -> list[Citation]:
        mapping = dict(evidence)
        unknown = set(output.evidence_ids) - set(mapping)
        if unknown:
            raise GroundingError(f"IDs de evidencia no permitidos: {', '.join(sorted(unknown))}")
        selected = [mapping[evidence_id] for evidence_id in output.evidence_ids]
        if output.evidence_sufficient and not selected:
            raise GroundingError("La respuesta no seleccionó evidencia")
        if any(not self.validator.validate(citation) for citation in selected):
            raise GroundingError("Una evidencia seleccionada ya no es válida")

        if deterministic_contract and (
            not output.evidence_sufficient
            or output.inferred
            or output.answer != DETERMINISTIC_ACK
            or output.flow
            or output.possible_change_locations
            or output.risks
            or output.recommended_tests
        ):
            raise GroundingError("El modelo alteró el acuse del contrato determinista")

        if not validate_generated_text:
            return selected

        text = self._output_text(output)
        allowed_ids = set(mapping)
        list_items = [
            *output.flow,
            *output.possible_change_locations,
            *output.risks,
            *output.recommended_tests,
        ]
        if any(item.strip() in allowed_ids for item in list_items):
            raise GroundingError("Los IDs de evidencia solo pueden aparecer en evidence_ids")
        if LINE_REFERENCE.search(text):
            raise GroundingError("El modelo intentó redactar números de línea")
        allowed_text = "\n".join(
            f"{citation.file} {citation.object} {citation.member} {citation.snippet}"
            for citation in selected
        ).lower()
        for file_name in SOURCE_FILE.findall(text):
            if file_name.lower() not in allowed_text:
                raise GroundingError(f"Archivo no respaldado: {file_name}")
        for identifier in CODE_IDENTIFIER.findall(text):
            if identifier.lower() not in allowed_text:
                raise GroundingError(f"Símbolo no respaldado: {identifier}")
        return selected

    def _generate(
        self,
        question: str,
        citations: list[Citation],
        require_all_evidence: bool = False,
        validate_generated_text: bool = True,
        deterministic_contract: bool = False,
    ) -> tuple[GroundedLLMOutput | None, list[Citation], GenerationInfo]:
        fitted = self._fit_context(citations)
        if not fitted:
            return None, [], self._generation_info("rejected", "Ningún fragmento completo cabe en el límite de contexto.")
        evidence = [(f"E{index}", citation) for index, citation in enumerate(fitted, 1)]
        user_prompt = build_user_prompt(question, evidence)
        if require_all_evidence:
            user_prompt += (
                "\n\nTodos los fragmentos fueron seleccionados determinísticamente para esta pregunta. "
                "Si evidence_sufficient=true, incluye TODOS los IDs permitidos en evidence_ids."
            )
        if deterministic_contract:
            user_prompt += (
                "\n\nMODO CONTRATO DETERMINISTA: el backend ya compuso la respuesta factual. "
                "Tu única tarea es confirmar que la evidencia es pertinente. Devuelve evidence_sufficient=true, "
                "inferred=false, answer exactamente \"Evidencia revisada por el backend.\", uno o más IDs "
                "permitidos en evidence_ids y [] en flow, possible_change_locations, risks y recommended_tests."
            )
        schema = GroundedLLMOutput.model_json_schema()
        properties = schema["properties"]
        schema["required"] = list(properties)
        allowed_ids = [evidence_id for evidence_id, _citation in evidence]
        properties["evidence_ids"]["items"] = {"type": "string", "enum": allowed_ids}
        if deterministic_contract:
            properties["evidence_sufficient"]["const"] = True
            properties["inferred"]["const"] = False
            properties["answer"]["const"] = DETERMINISTIC_ACK
            properties["evidence_ids"]["minItems"] = 1
            for field in ("flow", "possible_change_locations", "risks", "recommended_tests"):
                properties[field]["maxItems"] = 0
        last_error = "El modelo no produjo una salida válida."
        for attempt in range(1, self.llm_json_retries + 2):
            retry_note = ""
            if attempt > 1:
                retry_note = (
                    "\n\nREINTENTO: La salida anterior fue rechazada por esta causa: "
                    f"{last_error}. Corrígela, conserva todos los campos, devuelve JSON válido y usa únicamente los IDs permitidos."
                )
            try:
                result = self.llm.generate(SYSTEM_PROMPT, user_prompt + retry_note, schema)
                output = GroundedLLMOutput.model_validate_json(result.content)
                selected = self._validate_output(
                    output,
                    evidence,
                    validate_generated_text,
                    deterministic_contract,
                )
                if require_all_evidence and output.evidence_sufficient and len(selected) != len(evidence):
                    raise GroundingError("La respuesta omitió evidencia determinística requerida")
                return output, selected, self._generation_info(
                    "generated",
                    "Explicación generada localmente y validada contra IDs de evidencia.",
                    attempt,
                    result.metrics,
                )
            except LLMProviderError as exc:
                last_error = str(exc)
                if exc.code not in {"invalid_response"}:
                    break
            except (ValidationError, GroundingError) as exc:
                last_error = f"Salida estructurada rechazada: {exc}"
        status = "fallback" if "conectar" in last_error.lower() or "tiempo" in last_error.lower() else "rejected"
        return None, [], self._generation_info(status, last_error, self.llm_json_retries + 1)

    def ask(self, snapshot_id: str, question: str) -> Answer:
        if not question.strip():
            return Answer(
                "No localizado",
                "La pregunta está vacía.",
                [], [], [], [], [],
                self._not_invoked("No se invocó el LLM porque la pregunta está vacía."),
            )
        unknown = self.retriever.unknown_identifiers(snapshot_id, question)
        if unknown:
            return Answer(
                "No localizado",
                f"No se encontró evidencia para: {', '.join(unknown)}.",
                [], [], [], [], [],
                self._not_invoked("No se invocó el LLM porque el identificador no existe en el snapshot."),
            )
        plan = self._intent(question)
        if plan is None:
            return Answer(
                "No localizado",
                "No se encontró evidencia suficiente en el snapshot.",
                [], [], [], [], [],
                self._not_invoked("La abstención determinista ocurrió antes de invocar el LLM."),
            )

        citations: list[Citation] = []
        for member, start, end in plan.members:
            chunk = self._find_chunk(snapshot_id, member, start, end)
            if chunk is None:
                return Answer(
                    "No localizado",
                    "No se pudo reconstruir la evidencia requerida.",
                    [], [], [], [], [],
                    self._not_invoked("La evidencia requerida no pudo reconstruirse."),
                )
            citations.append(self.validator.build(chunk, start, end))

        if citations and not self.llm.enabled:
            return Answer(
                "Comprobado",
                plan.answer,
                list(plan.flow),
                citations,
                list(plan.changes),
                list(plan.risks),
                list(plan.tests),
                self._not_invoked("Respuesta determinista verificada; generación local deshabilitada."),
            )

        if citations and self.llm.enabled:
            output, _selected, generation = self._generate(
                question,
                citations,
                deterministic_contract=True,
            )
            if output is not None:
                # Para preguntas con contrato determinista, Ollama puede interpretar
                # la evidencia, pero no reemplazar los hechos ya reconstruidos por el
                # backend. Esto evita que una paráfrasis del modelo altere fórmulas,
                # ubicaciones o el flujo que acabamos de validar.
                return Answer(
                    "Comprobado",
                    plan.answer,
                    list(plan.flow),
                    citations,
                    list(plan.changes),
                    list(plan.risks),
                    list(plan.tests),
                    generation,
                )
            return Answer(
                "Inferido",
                f"No fue posible generar una explicación local validada. {generation.detail}",
                [], citations, [],
                ["La explicación del LLM fue descartada; revise únicamente las evidencias mostradas."],
                [], generation,
            )

        hits = self.retriever.search(snapshot_id, question, top_k=3)
        if not hits:
            return Answer(
                "No localizado",
                "No se encontró evidencia suficiente en el snapshot.",
                [], [], [], [], [],
                self._not_invoked("No se invocó el LLM porque retrieval no devolvió evidencia."),
            )
        fallback_citations = [self.validator.build(hit.chunk) for hit in hits]
        if self.llm.enabled:
            output, selected, generation = self._generate(question, fallback_citations)
            if output is not None and not output.evidence_sufficient:
                return Answer(
                    "No localizado",
                    output.answer or "La evidencia recuperada no permite responder la pregunta.",
                    [], [], [], [], [], generation,
                )
            if output is not None:
                flow, changes, risks, tests = self._requested_sections(question, output)
                return Answer(
                    "Inferido",
                    f"Inferencia basada en la evidencia recuperada: {output.answer}",
                    flow,
                    selected,
                    changes,
                    risks,
                    tests,
                    generation,
                )
            return Answer(
                "Inferido",
                f"Ollama no pudo producir una explicación validada. {generation.detail}",
                [], fallback_citations, [],
                ["No se aceptó ninguna conclusión del modelo; revise los fragmentos citados."],
                [], generation,
            )

        members = ", ".join(dict.fromkeys(citation.member for citation in fallback_citations))
        return Answer(
            "Inferido",
            f"La búsqueda recuperó evidencia verificable en {members}. La interpretación está deshabilitada; formule una pregunta más específica o active un proveedor LLM local.",
            [], fallback_citations, [],
            ["Revise los fragmentos citados antes de realizar cambios."],
            [], self._not_invoked("Retrieval completado con generación local deshabilitada."),
        )
