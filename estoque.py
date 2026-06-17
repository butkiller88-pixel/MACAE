import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Saldo de Estoque — Macaé", layout="wide")

st.title("📦 Saldo Atual de Materiais")

URL = "https://docs.google.com/spreadsheets/d/1peB38TTNhp_FS42mpZ85wJCeqhTl5w3lXdGJHruPRXw/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)

    # 1. Carregar as bases de dados
    with st.spinner("Calculando saldos em tempo real..."):
        df_ent = conn.read(spreadsheet=URL, worksheet="ENTRADA", ttl="10m")
        df_sai = conn.read(spreadsheet=URL, worksheet="SAÍDA", ttl="10m")
        df_materiais = conn.read(spreadsheet=URL, worksheet="MATERIAS SIEGI", ttl="1h")

    # 2. Processar Entradas (Somar por descrição)
    # Ajustamos os nomes das colunas conforme sua planilha: 'DESCRIÇÃO' e 'QNT.'
    entradas_soma = df_ent.groupby('DESCRIÇÃO')['QNT.'].sum().reset_index()
    entradas_soma.columns = ['Descrição', 'Total_Entrada']

    # 3. Processar Saídas (Somar por descrição)
    # Na aba Saída a coluna também é 'DESCRIÇÃO' e 'QNT.'
    saidas_soma = df_sai.groupby('DESCRIÇÃO')['QNT.'].sum().reset_index()
    saidas_soma.columns = ['Descrição', 'Total_Saida']

    # 4. Cruzar dados com a lista oficial de Materiais
    estoque = df_materiais[['Descrição', 'Unidade']].copy()
    estoque = estoque.merge(entradas_soma, on='Descrição', how='left')
    estoque = estoque.merge(saidas_soma, on='Descrição', how='left')

    # 5. Calcular Saldo Final
    estoque['Total_Entrada'] = estoque['Total_Entrada'].fillna(0)
    estoque['Total_Saida'] = estoque['Total_Saida'].fillna(0)
    estoque['Saldo Atual'] = estoque['Total_Entrada'] - estoque['Total_Saida']

    # --- INTERFACE ---
    st.info("O saldo é calculado subtraindo as Saídas das Entradas registradas.")

    # Filtro de busca
    busca = st.text_input("🔍 Filtrar material no estoque:", placeholder="Ex: Cimento, Tubo, Areia...")
    if busca:
        estoque = estoque[estoque['Descrição'].str.contains(busca, case=False, na=False)]

    # Destaque para itens zerados ou negativos
    def color_saldo(val):
        color = 'red' if val <= 0 else 'white'
        return f'color: {color}'

    st.subheader("Tabela de Inventário")
    st.dataframe(
        estoque.style.applymap(color_saldo, subset=['Saldo Atual']),
        use_container_width=True,
        hide_index=True
    )

    # Métricas Rápidas
    c1, c2 = st.columns(2)
    c1.metric("Total de Itens no Catálogo", len(estoque))
    c2.metric("Itens com Saldo Positivo", len(estoque[estoque['Saldo Atual'] > 0]))

except Exception as e:
    st.error("Erro ao calcular estoque. Verifique se as colunas 'DESCRIÇÃO' e 'QNT.' existem em ambas as abas.")
    st.info(f"Detalhe: {e}")
