@echo off
echo Iniciando Zapia Estoque...
pip install -r requirements_estoque.txt
streamlit run app_controle_estoque.py
pause
