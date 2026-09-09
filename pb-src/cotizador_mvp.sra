$PBExportHeader$cotizador_mvp.sra
$PBExportComments$Application object del cotizador demostrativo
forward
global type cotizador_mvp from application
end type
global transaction sqlca
global dynamicdescriptionarea sqlda
global dynamicstagingarea sqlsa
global error error
global message message
end forward

global variables
end variables

global type cotizador_mvp from application
string appname = "cotizador_mvp"
end type
global cotizador_mvp cotizador_mvp

on cotizador_mvp.create
appname = "cotizador_mvp"
message = create message
sqlca = create transaction
sqlda = create dynamicdescriptionarea
sqlsa = create dynamicstagingarea
error = create error
end on

on cotizador_mvp.destroy
destroy(sqlca)
destroy(sqlda)
destroy(sqlsa)
destroy(error)
destroy(message)
end on

event open;
open(w_cotizador_mvp)
end event

