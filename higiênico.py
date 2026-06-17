import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Histórico de Obra — Macaé", layout="wide")

st.title("📑 Histórico de Movimentações")

URL = "https://docs.google.com/spreadsheets/d/1peB38TTNhp_FS42mpZ85wJCeqhTl5w3lXdGJHruPRXw/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)

    # Abas de visualização
    tipo_historico = st.radio("Escolha o Histórico:", ["📥 Entradas (Recebimentos)", "📤 Saídas (Canteiro)"], horizontal=True)

    if tipo_historico == "📥 Entradas (Recebimentos)":
        st.subheader("Últimas Entradas de Materiais")
        # Lê a aba ENTRADA
        df_ent = conn.read(spreadsheet=URL, worksheet="ENTRADA", ttl="5m")
        
        # Filtro de busca simples
        busca_ent = st.text_input("🔍 Buscar por fornecedor ou material (Entrada):")
        if busca_ent:
            df_ent = df_ent[df_ent.astype(str).apply(lambda x: x.str.contains(busca_ent, case=False)).any(axis=1)]
        
        # Mostra os dados (os mais recentes primeiro)
        st.dataframe(df_ent.iloc[::-1], use_container_width=True, hide_index=True)

    else:
        st.subheader("Últimas Saídas para o Canteiro")
        # Lê a aba SAÍDA
        df_sai = conn.read(spreadsheet=URL, worksheet="SAÍDA", ttl="5m")
        
        # Filtro de busca simples
        busca_sai = st.text_input("🔍 Buscar por funcionário ou material (Saída):")
        if busca_sai:
            df_sai = df_sai[df_sai.astype(str).apply(lambda x: x.str.contains(busca_sai, case=False)).any(axis=1)]
        
        # Mostra os dados (os mais recentes primeiro)
        st.dataframe(df_sai.iloc[::-1], use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Não foi possível carregar o histórico.")
    st.info(f"Detalhe: {e}")
