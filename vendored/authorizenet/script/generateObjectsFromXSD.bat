@ECHO OFF

@REM Script to generate the python contract from XSD
@REM Requires pyxb module to be installed and available in path

@ECHO  Running Pyxbgen on %DATE%-%TIME%
where python > NUL
IF "0"=="%ERRORLEVEL%" (
    @ECHO Found python
) ELSE (
    @ECHO Unable to find python. Make sure python is installed. 
    EXIT /b 1
)
where pyxbgen > %TEMP%\pyxbgenpath.txt
IF "0"=="%ERRORLEVEL%" (
    @ECHO Found pyxbgen
) ELSE (
    @ECHO Unable to find pyxbgen. Make sure pyxb package is installed. 
    EXIT /b 1
)
SET XSDPATH=https://apitest.authorize.net/xml/v1/schema/AnetApiSchema.xsd
SET CONTRACTSDIR=authorizenet
SET CONTRACTSFILE=apicontractsv1
SET /p PYXBGENPATH=< %TEMP%\pyxbgenpath.txt
SET TEMPFILE=binding

@ECHO Using pyxb from "%PYXBGENPATH%"
IF EXIST "%TEMPFILE%.py" (
    DEL "%TEMPFILE%.py" > NUL
)

python "%PYXBGENPATH%" -u %XSDPATH% -m %TEMPFILE%
IF "0"=="%ERRORLEVEL%" (
    IF EXIST "%CONTRACTSDIR%\%CONTRACTSFILE%.old" (
        DEL "%CONTRACTSDIR%\%CONTRACTSFILE%.old" > NUL
    )
    IF EXIST "%CONTRACTSDIR%\%CONTRACTSFILE%.py" (
        DEL "%CONTRACTSDIR%\%CONTRACTSFILE%.py" > NUL
    )
    MOVE "%TEMPFILE%.py" "%CONTRACTSDIR%\%CONTRACTSFILE%.py" > NUL
    @ECHO Bindings have been successfully generated from XSD in the file authorizenet\%CONTRACTSFILE%.py
    @ECHO Old contracts have been moved to .old
) ELSE (
    @ECHO Found python
    @ECHO Error generating bindings from XSD. Review the errors and rerun the script.
    EXIT /b 1
)

EXIT /b 0
