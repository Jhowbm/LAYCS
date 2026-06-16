@echo off
chcp 65001 >nul
echo Criando atalho na area de trabalho...

set SCRIPT_PATH=%~dp0INICIAR.bat
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT_PATH=%DESKTOP%\Flashscore Lay Analyzer.lnk

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%SCRIPT_PATH%'; $s.WorkingDirectory = '%~dp0'; $s.Description = 'Flashscore Lay Analyzer - Metodo de Ciclos'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo.
    echo [SUCESSO] Atalho criado na area de trabalho!
    echo Procure por: Flashscore Lay Analyzer.lnk
    echo.
) else (
    echo.
    echo [ERRO] Nao foi possivel criar o atalho.
    echo Voce pode usar o arquivo INICIAR.bat diretamente na pasta do projeto.
    echo.
)

pause