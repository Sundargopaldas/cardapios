@echo off
echo Iniciando o servidor do CardapioAI...
echo.

:: Criar pastas necessarias se nao existirem
if not exist "uploads" mkdir uploads
if not exist "layouts" mkdir layouts
if not exist "geradas" mkdir geradas
if not exist "public\menus" mkdir public\menus

:: Iniciar o servidor
python server.py

:: Se o Python nao for encontrado, mostrar mensagem de erro
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Erro: Python nao encontrado. Por favor, instale o Python e tente novamente.
    echo Pressione qualquer tecla para sair...
    pause > nul
) 