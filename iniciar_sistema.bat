@echo off
title Sistema de Controle Financeiro
cd /d "%~dp0"

echo ======================================================
echo    Iniciando Sistema de Controle Financeiro
echo ======================================================

if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual 'venv' nao encontrado!
    echo Execute a instalacao do ambiente antes de iniciar.
    pause
    exit /b 1
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Iniciando aplicacao Streamlit em http://localhost:8501 ...
streamlit run app.py --server.address 0.0.0.0

pause
