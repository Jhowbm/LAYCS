@echo off
chcp 65001 >nul
title Flashscore Lay Analyzer - Inicialização Automática

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     FLASHSCORE LAY ANALYZER - MÉTODO DE CICLOS              ║
echo ║     Inicialização Automática - Um Clique para Começar       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/5] Verificando ambiente virtual...
if not exist "venv\Scripts\activate.bat" (
    echo    ⚠ Ambiente virtual não encontrado. Criando...
    python -m venv venv
    echo    ✅ Ambiente virtual criado!
) else (
    echo    ✅ Ambiente virtual encontrado!
)

echo.
echo [2/5] Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo    ✅ Ambiente virtual ativado!

echo.
echo [3/5] Verificando dependências...
pip install -q flask selenium beautifulsoup4 pandas webdriver-manager openpyxl
echo    ✅ Dependências instaladas/atualizadas!

echo.
echo [4/5] Verificando arquivos do sistema...
if not exist "ciclos_manager.py" (
    echo    ⚠ Arquivo ciclos_manager.py não encontrado!
    echo    Certifique-se de que todos os arquivos estão no diretório.
    pause
    exit /b 1
)
if not exist "app.py" (
    echo    ⚠ Arquivo app.py não encontrado!
    echo    Certifique-se de que todos os arquivos estão no diretório.
    pause
    exit /b 1
)
echo    ✅ Todos os arquivos encontrados!

echo.
echo [5/5] Iniciando aplicação web...
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     APLICAÇÃO INICIADA!                                      ║
echo ║     Acesse no navegador: http://localhost:5000              ║
echo ║                                                              ║
echo ║     Pressione CTRL+C para parar o servidor                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

python app.py

pause