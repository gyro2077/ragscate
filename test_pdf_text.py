import pymupdf as fitz
doc = fitz.open("reglas-del-negocio-pdf/Reglas de Negocio - Seguros de Gyro-signed.pdf")
text = ""
for page in doc:
    text += page.get_text()

lines = text.splitlines()
for i, line in enumerate(lines):
    print(f"{i+1:03d}: {line}")
