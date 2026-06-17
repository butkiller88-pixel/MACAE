import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Cadastro de Entrada — Macaé", layout="centered")

st.title("📥 Cadastro de Entrada de Material")

# Link da sua planilha
URL = "https://docs.google.com/spreadsheets/d/1peB38TTNhp_FS42mpZ85wJCeqhTl5w3lXdGJHruPRXw/edit"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)

    with st.form("entrada_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        data = col1.date_input("Data do Recebimento", date.today())
        # Categorias baseadas no seu histórico
        categoria = col1.selectbox("Categoria", ['AGREGADOS', 'CIMENTO', 'ELÉTRICA', 'FERRAGENS', 'FERRAMENTA', 'MADEIRA', 'TUBOS E CONEXÕES', 'OUTROS'])
        descricao = col1.text_input("Descrição do Material (Ex: Cimento CP-II)")
        
        quantidade = col2.number_input("Quantidade", min_value=0.0, step=0.1)
        medida = col2.text_input("Unidade de Medida (Ex: SACOS, m³, un)")
        fornecedor = col2.text_input("Fornecedor")
        nota_fiscal = col2.text_input("Nº Nota Fiscal / Requisição")
        
        submit = st.form_submit_button("✅ Gravar Entrada no Drive")

        if submit:
            if descricao and quantidade > 0:
                # Monta a linha exatamente como as colunas da sua aba "ENTRADA"
                nova_linha = pd.DataFrame([{
                    "Data": data.strftime("%d/%m/%Y"),
                    "CATEGORIA": categoria,
                    "DESCRIÇÃO": descricao.upper(),
                    "QNT.": quantidade,
                    "MEDIDA": medida.upper(),
                    "FORNECEDOR": fornecedor.upper(),
                    "NOTA / REQ": nota_fiscal
                }])
                
                # Salva na aba correta
                conn.create(spreadsheet=URL, worksheet="ENTRADA", data=nova_linha)
                st.success(f"Sucesso! {descricao.upper()} registrado no Drive.")
            else:
                st.warning("⚠️ Preencha a descrição e a quantidade.")

except Exception as e:
    st.error("Erro de conexão. Verifique se a planilha permite edição via link.")
    st.info(f"Detalhe: {e}")
