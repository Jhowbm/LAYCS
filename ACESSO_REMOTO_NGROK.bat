@echo off
chcp 65001 >nul
title Acesso Remoto com ngrok

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     ACESSO REMOTO COM NGROK                                  ║
echo ║     Acesse seu sistema de qualquer lugar do mundo!            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/4] Verificando se ngrok esta instalado...
where ngrok >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    ngrok nao encontrado!
    echo.
    echo Para instalar ngrok:
    echo    1. Acesse: https://ngrok.com/download
    echo    2. Baixe a versao para Windows
    echo    3. Extraia para uma pasta (ex: C:\ngrok)
    echo    4. Adicione ao PATH do sistema
    echo.
    echo Ou use opcoes alternativas abaixo.
    echo.
    pause
    exit /b 1
)

echo    ngrok encontrado!
echo.

echo [2/4] Iniciando o sistema Flashscore Lay Analyzer...
echo    (Em outra janela, execute: INICIAR.bat)
echo.
echo    Pressione qualquer tecla quando o sistema estiver rodando...
pause >nul

echo.
echo [3/4] Criando tunel seguro com ngrok...
echo    Isso criara um link publico para seu sistema local
echo.

ngrok http 5000

echo.
echo [4/4] Se ngrok fechou, aqui estao as alternativas:
echo.
echo ALTERNATIVA 1 - Servicos gratuitos de deploy:
echo    - Render: https://render.com
echo    - Railway: https://railway.app
echo    - PythonAnywhere: https://www.pythonanywhere.com
echo.
echo ALTERNATIVA 2 - Tunnels gratuitos:
echo    - Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
echo    - localtunnel: https://localtunnel.github.io/www/
echo.
echo ALTERNATIVA 3 - VPN:
echo    - Use VPN para acessar sua rede local de forma segura
echo.

pause