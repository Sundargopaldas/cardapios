@echo off
REM Verifica se foi passada uma mensagem de commit
IF "%~1"=="" (
    echo ⚠️  Voce precisa informar uma mensagem de commit.
    echo Exemplo: sobe "minha mensagem"
    exit /b
)

REM Junta todos os argumentos em uma única string para o commit
set MSG=%1
shift
:loop
IF "%~1"=="" GOTO continuar
set MSG=%MSG% %1
shift
GOTO loop

:continuar
echo 📁 Adicionando arquivos...
git add .

echo 💬 Commitando com a mensagem: %MSG%
git commit -m "%MSG%"

echo 🚀 Enviando para o GitHub...
git push origin main

echo ✅ Concluído!
