import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Saída de Material — Macaé", layout="centered")

st.title("📤 Registro de Saída (Canteiro)")

# Link da sua planilha
URL = "https://docs.google.com/spreadsheets/d/1peB38TTNhp_FS42mpZ85wJCeqhTl5w3lXdGJHruPRXw/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)

    # 1. Busca as listas de Funcionários e Materiais direto das suas abas
    df_colab = conn.read(spreadsheet=URL, worksheet="COLABORADORES", ttl="30m")
    df_materiais = conn.read(spreadsheet=URL, worksheet="MATERIAS SIEGI", ttl="1h")

    with st.form("saida_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        data_s = col1.date_input("Data da Retirada", date.today())
        
        # Selectbox com busca: seleciona o material da sua lista SIEGI
        material_s = col1.selectbox("Material Retirado", df_materiais['Descrição'].dropna().unique())
        
        # Selectbox com busca: seleciona o funcionário da sua lista oficial
        funcionario_s = col1.selectbox("Funcionário Responsável", df_colab['FUNCIONÁRIO'].dropna().unique())
        
        quantidade_s = col2.number_input("Quantidade", min_value=0.0, step=1.0)
        destino_s = col2.text_input("Destino (Ex: Rua Equador, Trecho 2)")
        servico_s = col2.text_input("Serviço (Ex: Rede de Esgoto)")
        obs_s = col2.text_area("Observações Adicionais")
        
        submit_s = st.form_submit_button("🚀 Autorizar e Gravar Saída")

        if submit_s:
            if quantidade_s > 0:
                # Monta a linha conforme as colunas da sua aba "SAÍDA"
                # DATA, CATEGORIA, DESCRIÇÃO, QNT., UND., FUNCIONARIO, FUNÇÃO, DESTINO, SERVICOS, OBS
                nova_saida = pd.DataFrame([{
                    "DATA": data_s.strftime("%d/%m/%Y"),
                    "DESCRIÇÃO": material_s,
                    "QNT.": quantidade_s,
                    "FUNCIONARIO": funcionario_s,
                    "DESTINO": destino_s.upper(),
                    "SERVICOS ": serv_sai.upper() if 'serv_sai' in locals() else servico_s.upper(),
                    "OBS": obs_s.upper()
                }])
                
                # Salva na aba SAÍDA
                conn.create(spreadsheet=URL, worksheet="SAÍDA", data=nova_saida)
                st.success(f"Saída de {quantidade_s} {material_s} para {funcionario_s} registrada!")
            else:
                st.warning("⚠️ Informe a quantidade retirada.")

except Exception as e:
    st.error("Erro ao carregar listas do Drive.")
    st.info(f"Detalhe: {e}")
