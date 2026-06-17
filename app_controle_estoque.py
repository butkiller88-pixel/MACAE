import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os

# Configuração da página
st.set_page_config(page_title="Controle de Macae - almoxarifado", layout="wide")

# --- BANCO DE DADOS ---
DB_NAME = "estoque_obras.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Cadastro de Materiais
    c.execute('''CREATE TABLE IF NOT EXISTS materiais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    unidade TEXT,
                    categoria TEXT)''')
    # Cadastro de Funcionários
    c.execute('''CREATE TABLE IF NOT EXISTS funcionarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    cargo TEXT)''')
    # Cadastro de Ruas/Localizações
    c.execute('''CREATE TABLE IF NOT EXISTS ruas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL)''')
    # Movimentações (Entrada/Saída)
    c.execute('''CREATE TABLE IF NOT EXISTS movimentacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    tipo TEXT, -- 'Entrada' ou 'Saída'
                    material_id INTEGER,
                    quantidade REAL,
                    funcionario_id INTEGER,
                    rua_id INTEGER,
                    observacao TEXT,
                    FOREIGN KEY(material_id) REFERENCES materiais(id),
                    FOREIGN KEY(funcionario_id) REFERENCES funcionarios(id),
                    FOREIGN KEY(rua_id) REFERENCES ruas(id))''')
    conn.commit()
    conn.close()

def run_query(query, params=(), commit=False):
    conn = sqlite3.connect(DB_NAME)
    if commit:
        conn.execute(query, params)
        conn.commit()
        conn.close()
    else:
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

init_db()

# --- ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- MENU LATERAL ---
st.sidebar.title("🏗️ Zapia Estoque")
menu = st.sidebar.selectbox("Navegação", ["Resumo de Saldo", "Registrar Entrada", "Registrar Saída", "Histórico", "Cadastros"])

# --- LÓGICA DE SALDO ---
def get_saldo():
    query = """
    SELECT 
        m.nome as Material,
        m.unidade as Unidade,
        SUM(CASE WHEN mov.tipo = 'Entrada' THEN mov.quantidade ELSE 0 END) -
        SUM(CASE WHEN mov.tipo = 'Saída' THEN mov.quantidade ELSE 0 END) as Saldo
    FROM materiais m
    LEFT JOIN movimentacoes mov ON m.id = mov.material_id
    GROUP BY m.id
    """
    return run_query(query)

# --- PÁGINAS ---

if menu == "Resumo de Saldo":
    st.title("📊 Controle de Saldo Atual")
    df_saldo = get_saldo()
    
    if df_saldo.empty or df_saldo['Material'].isnull().all():
        st.warning("Nenhum material cadastrado ou sem movimentações.")
    else:
        # Métricas rápidas
        cols = st.columns(min(len(df_saldo), 4))
        for i, row in df_saldo.head(4).iterrows():
            with cols[i % 4]:
                st.metric(row['Material'], f"{row['Saldo']} {row['Unidade']}")
        
        st.divider()
        st.dataframe(df_saldo, use_container_width=True)

elif menu == "Registrar Entrada":
    st.title("📥 Entrada de Material")
    
    materiais = run_query("SELECT id, nome FROM materiais")
    ruas = run_query("SELECT id, nome FROM ruas")
    
    if materiais.empty:
        st.error("Cadastre materiais primeiro!")
    else:
        with st.form("form_entrada"):
            col1, col2 = st.columns(2)
            with col1:
                mat_id = st.selectbox("Material", materiais['id'], format_func=lambda x: materiais[materiais['id']==x]['nome'].values[0])
                qtd = st.number_input("Quantidade", min_value=0.1, step=0.1)
                data_mov = st.date_input("Data", datetime.now())
            with col2:
                rua_id = st.selectbox("Localização (Rua)", ruas['id'] if not ruas.empty else [None], 
                                    format_func=lambda x: ruas[ruas['id']==x]['nome'].values[0] if x else "Nenhuma cadastrada")
                obs = st.text_area("Observações")
            
            if st.form_submit_button("Confirmar Entrada"):
                run_query("INSERT INTO movimentacoes (data, tipo, material_id, quantidade, rua_id, observacao) VALUES (?, 'Entrada', ?, ?, ?, ?)",
                          (data_mov.strftime('%Y-%m-%d'), mat_id, qtd, rua_id, obs), commit=True)
                st.success("Entrada registrada com sucesso!")

elif menu == "Registrar Saída":
    st.title("📤 Saída de Material")
    
    materiais = run_query("SELECT id, nome FROM materiais")
    funcionarios = run_query("SELECT id, nome FROM funcionarios")
    
    if materiais.empty or funcionarios.empty:
        st.error("Cadastre materiais e funcionários primeiro!")
    else:
        with st.form("form_saida"):
            col1, col2 = st.columns(2)
            with col1:
                mat_id = st.selectbox("Material", materiais['id'], format_func=lambda x: materiais[materiais['id']==x]['nome'].values[0])
                qtd = st.number_input("Quantidade Retirada", min_value=0.1, step=0.1)
                data_mov = st.date_input("Data", datetime.now())
            with col2:
                func_id = st.selectbox("Funcionário Responsável", funcionarios['id'], format_func=lambda x: funcionarios[funcionarios['id']==x]['nome'].values[0])
                obs = st.text_area("Observações / Destino")
            
            # Checar saldo antes de permitir saída
            saldo_atual = get_saldo()
            mat_nome = materiais[materiais['id']==mat_id]['nome'].values[0]
            saldo_val = saldo_atual[saldo_atual['Material'] == mat_nome]['Saldo'].values[0] if mat_nome in saldo_atual['Material'].values else 0
            
            if st.form_submit_button("Confirmar Saída"):
                if qtd > saldo_val:
                    st.error(f"Saldo insuficiente! Saldo atual: {saldo_val}")
                else:
                    run_query("INSERT INTO movimentacoes (data, tipo, material_id, quantidade, funcionario_id, observacao) VALUES (?, 'Saída', ?, ?, ?, ?)",
                              (data_mov.strftime('%Y-%m-%d'), mat_id, qtd, func_id, obs), commit=True)
                    st.success("Saída registrada!")

elif menu == "Histórico":
    st.title("📜 Histórico de Movimentações")
    query = """
    SELECT 
        mov.data as Data,
        mov.tipo as Tipo,
        m.nome as Material,
        mov.quantidade as Quantidade,
        f.nome as Funcionário,
        r.nome as Rua,
        mov.observacao as Obs
    FROM movimentacoes mov
    JOIN materiais m ON mov.material_id = m.id
    LEFT JOIN funcionarios f ON mov.funcionario_id = f.id
    LEFT JOIN ruas r ON mov.rua_id = r.id
    ORDER BY mov.id DESC
    """
    df_hist = run_query(query)
    st.dataframe(df_hist, use_container_width=True)

elif menu == "Cadastros":
    st.title("⚙️ Gerenciar Cadastros")
    
    aba1, aba2, aba3 = st.tabs(["Materiais", "Funcionários", "Ruas"])
    
    with aba1:
        st.subheader("Novo Material")
        with st.form("cad_mat"):
            nome_mat = st.text_input("Nome do Material")
            unid_mat = st.text_input("Unidade (ex: un, kg, m)")
            cat_mat = st.text_input("Categoria")
            if st.form_submit_button("Salvar Material"):
                run_query("INSERT INTO materiais (nome, unidade, categoria) VALUES (?, ?, ?)", (nome_mat, unid_mat, cat_mat), commit=True)
                st.rerun()
        st.write("Materiais Cadastrados:")
        st.dataframe(run_query("SELECT * FROM materiais"), use_container_width=True)

    with aba2:
        st.subheader("Novo Funcionário")
        with st.form("cad_func"):
            nome_func = st.text_input("Nome Completo")
            cargo_func = st.text_input("Cargo")
            if st.form_submit_button("Salvar Funcionário"):
                run_query("INSERT INTO funcionarios (nome, cargo) VALUES (?, ?)", (nome_func, cargo_func), commit=True)
                st.rerun()
        st.write("Funcionários:")
        st.dataframe(run_query("SELECT * FROM funcionarios"), use_container_width=True)

    with aba3:
        st.subheader("Nova Rua / Localização")
        with st.form("cad_rua"):
            nome_rua = st.text_input("Nome da Rua/Setor")
            if st.form_submit_button("Salvar Rua"):
                run_query("INSERT INTO ruas (nome) VALUES (?)", (nome_rua,), commit=True)
                st.rerun()
        st.write("Localizações:")
        st.dataframe(run_query("SELECT * FROM ruas"), use_container_width=True)

st.sidebar.divider()
st.sidebar.caption("OMEGA - GRENDE MACAE")
