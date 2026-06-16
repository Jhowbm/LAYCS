@echo off
chcp 65001 >nul
title Descobrir IP Local para Acesso Remoto

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     DESCOBRIR IP LOCAL - ACESSO REMOTO                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [1/2] Descobrindo seu IP local...
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R "IPv4"') do (
    set IP=%%A
    goto :found
)

:found
set IP=%IP: =%

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     SEU IP LOCAL: %IP%                                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo [2/2] Informacoes de acesso:
echo.
echo Acesso LOCAL (apenas seu computador):
echo    http://localhost:5000
echo.
echo Acesso REDE LOCAL (mesma rede Wi-Fi):
echo    http://%IP%:5000
echo.
echo Acesso REMOTO (internet):
echo    Requer configuracao adicional do roteador
echo.

echo ╔══════════════════════════════════════════════════════════════╗
echo ║     COMO USAR O IP PARA ACESSO REMOTO:                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 1. Inicie o sistema com INICIAR.bat
echo 2. No celular/tablet (mesma rede Wi-Fi):
echo    - Abra o navegador
echo    - Digite: http://%IP%:5000
echo    - Pronto! Voce tera acesso ao sistema
echo.
echo 3. Para acesso de fora da rede (internet):
echo    - Requer configuracao de port forwarding no roteador
echo    - Ou usar servicos como ngrok (ver abaixo)
echo.

pause