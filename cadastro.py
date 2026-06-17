import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Cadastro de Materiais — Macaé", layout="centered")

st.title("📦 Cadastro de Novo Material (Catálogo)")

# Link da sua planilha
URL = "https://docs.google.com/spreadsheets/d/1peB38TTNhp_FS42mpZ85wJCeqhTl5w3lXdGJHruPRXw/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)

    st.info("Use este formulário para adicionar itens ao catálogo **MATERIAS SIEGI**.")

    with st.form("material_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        codigo = col1.text_input("Código do Material (Opcional)")
        descricao = col1.text_input("Nome/Descrição Completa do Material")
        
        unidade = col2.text_input("Unidade de Medida (Ex: MT, UN, SACO, KG)")
        cod_fiscal = col2.text_input("Cód. Produto Fiscal (Opcional)")
        
        submit_m = st.form_submit_button("➕ Adicionar ao Catálogo")

        if submit_m:
            if descricao and unidade:
                # Monta a linha conforme as colunas da aba "MATERIAS SIEGI"
                # Código, Descrição, Unidade, Cód. Produto Fiscal
                novo_material = pd.DataFrame([{
                    "Código": codigo,
                    "Descrição": descricao.upper(),
                    "Unidade": unidade.upper(),
                    "Cód. Produto Fiscal": cod_fiscal
                }])
                
                # Salva na aba de catálogo
                conn.create(spreadsheet=URL, worksheet="MATERIAS SIEGI", data=novo_material)
                st.success(f"Material '{descricao.upper()}' adicionado com sucesso ao catálogo!")
            else:
                st.warning("⚠️ Nome do material e Unidade são obrigatórios.")

    # Exibição rápida dos últimos materiais cadastrados
    st.divider()
    st.subheader("📋 Materiais Recentes no Catálogo")
    df_lista = conn.read(spreadsheet=URL, worksheet="MATERIAS SIEGI", ttl="5m")
    st.dataframe(df_lista.tail(10), use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Erro ao acessar o catálogo de materiais.")
    st.info(f"Detalhe: {e}")
