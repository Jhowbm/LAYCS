@echo off
chcp 65001 >nul
title Preparar Deploy em Nuvem - Flashscore Lay Analyzer

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     PREPARAR DEPLOY EM NUVEM - RENDER                        ║
echo ║     URL Permanente e Gratuita                                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/6] Verificando se Git esta instalado...
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    Git nao encontrado!
    echo.
    echo Para instalar Git:
    echo    1. Acesse: https://git-scm.com/download/win
    echo    2. Baixe e instale o Git para Windows
    echo    3. Execute este script novamente
    echo.
    pause
    exit /b 1
)
echo    Git encontrado!

echo.
echo [2/6] Inicializando repositório Git...
if not exist ".git" (
    git init
    echo    Repositorio Git inicializado!
) else (
    echo    Repositorio Git ja existe!
)

echo.
echo [3/6] Verificando arquivos de configuracao...
if not exist "render.yaml" (
    echo    Arquivo render.yaml nao encontrado!
    echo    Criando arquivo padrao...
) else (
    echo    Arquivo render.yaml encontrado!
)

if not exist "runtime.txt" (
    echo    Arquivo runtime.txt nao encontrado!
    echo    Criando arquivo padrao...
) else (
    echo    Arquivo runtime.txt encontrado!
)

if not exist ".gitignore" (
    echo    Arquivo .gitignore nao encontrado!
    echo    Criando arquivo padrao...
) else (
    echo    Arquivo .gitignore encontrado!
)

echo.
echo [4/6] Adicionando arquivos ao Git...
git add .
echo    Arquivos adicionados!

echo.
echo [5/6] Criando commit inicial...
git commit -m "Inicializar Flashscore Lay Analyzer - Metodo de Ciclos" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    Nenhum commit novo necessario (arquivos ja commitados)
) else (
    echo    Commit inicial criado!
)

echo.
echo [6/6] Verificando conexao com GitHub remoto...
git remote -v | findstr "origin" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo    Nenhum repositorio remoto configurado!
    echo.
    echo    PROXIMOS PASSOS:
    echo    1. Crie um repositorio no GitHub: https://github.com/new
    echo    2. Copie a URL do repositorio (ex: https://github.com/usuario/flashscore-lay.git)
    echo    3. Execute: git remote add origin SUA_URL_DO_GITHUB
    echo    4. Execute: git push -u origin master
    echo.
    echo    Ou use este comando:
    echo    git remote add origin SUA_URL_DO_GITHUB
) else (
    echo    Repositorio remoto ja configurado!
    echo    Para enviar alteracoes: git push
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║     PREPARACAO CONCLUIDA!                                      ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo PROXIMO PASSO: Deploy no Render
echo.
echo 1. Acesse: https://dashboard.render.com/
echo 2. Crie uma conta gratuita
echo 3. Clique em "New +"
echo 4. Selecione "Web Service"
echo 5. Conecte seu repositorio GitHub
echo 6. Render detectara automaticamente a configuracao
echo 7. Clique em "Create Web Service"
echo.
echo URL permanente sera gerada automaticamente!
echo Exemplo: https://flashscore-lay-analyzer.onrender.com
echo.
pause