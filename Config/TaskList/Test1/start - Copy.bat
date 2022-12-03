chcp 65001
@echo off

cd %~dp0
python main.py


IF %errorlevel% NEQ 0 GOTO ERROR

:OK
ECHO [BAT FILE B] command success
GOTO END

:ERROR
ECHO [BAT FILE B] command failed
GOTO END

:END
IF %ERRORLEVEL% GEQ 0 EXIT /B %ERRORLEVEL%
EXIT /B 0