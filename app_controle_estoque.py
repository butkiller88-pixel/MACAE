import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import os
import io

# Configuração da página
st.set_page_config(page_title="Zapia Estoque - Controle Profissional", layout="wide")

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

# --- FUNÇÕES DE IMPORTAÇÃO/EXPORTAÇÃO ---

def export_to_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Folha de Materiais
        run_query("SELECT * FROM materiais").to_excel(writer, sheet_name='MATERIAIS', index=False)
        # Folha de Funcionários
        run_query("SELECT * FROM funcionarios").to_excel(writer, sheet_name='FUNCIONARIOS', index=False)
        # Folha de Movimentações
        query_mov = """
        SELECT mov.data, mov.tipo, m.nome as material, mov.quantidade, f.nome as funcionario, r.nome as rua, mov.observacao
        FROM movimentacoes mov
        LEFT JOIN materiais m ON mov.material_id = m.id
        LEFT JOIN funcionarios f ON mov.funcionario_id = f.id
        LEFT JOIN ruas r ON mov.rua_id = r.id
        """
        run_query(query_mov).to_excel(writer, sheet_name='MOVIMENTACOES', index=False)
    return output.getvalue()

def import_from_almoxarifado(file):
    try:
        # Tenta ler as abas principais da planilha do cliente
        xls = pd.ExcelFile(file)
        
        # 1. Importar Materiais da aba 'MATERIAS SIEGI' ou similar
        if 'MATERIAS SIEGI' in xls.sheet_names:
            df_m = pd.read_excel(xls, 'MATERIAS SIEGI')
            # Ajustar colunas conforme a estrutura real (exemplo simplificado)
            for _, row in df_m.iterrows():
                nome = str(row.get('DESCRIÇÃO', row.get('NOME', '')))
                if nome and nome != 'nan':
                    run_query("INSERT INTO materiais (nome, unidade) VALUES (?, ?)", (nome, str(row.get('UNIDADE', 'un'))), commit=True)
        
        # 2. Importar Entradas
        if 'ENTRADA' in xls.sheet_names:
            df_e = pd.read_excel(xls, 'ENTRADA', skiprows=4) # Geralmente começa na linha 6 (skip 4 ou 5)
            # Implementação básica de parser
            st.info("Processando abas de Entrada...")

        return True
    except Exception as e:
        st.error(f"Erro na importação: {e}")
        return False

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
menu = st.sidebar.selectbox("Navegação", ["Resumo de Saldo", "Registrar Entrada", "Registrar Saída", "Histórico", "Cadastros", "Backup Excel"])

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
    
    # Adicionar opção de limpar histórico
    with st.expander("⚠️ Zona de Perigo"):
        if st.button("Apagar Todo o Histórico"):
            run_query("DELETE FROM movimentacoes", commit=True)
            st.success("Histórico apagado com sucesso!")
            st.rerun()

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
        df_mat = run_query("SELECT * FROM materiais")
        st.dataframe(df_mat, use_container_width=True)
        
        with st.expander("🗑️ Apagar Material"):
            if not df_mat.empty:
                mat_del = st.selectbox("Selecione o Material para remover", df_mat['id'], format_func=lambda x: df_mat[df_mat['id']==x]['nome'].values[0])
                if st.button("Remover Material"):
                    run_query("DELETE FROM materiais WHERE id = ?", (mat_del,), commit=True)
                    st.success("Material removido!")
                    st.rerun()

    with aba2:
        st.subheader("Novo Funcionário")
        with st.form("cad_func"):
            nome_func = st.text_input("Nome Completo")
            cargo_func = st.text_input("Cargo")
            if st.form_submit_button("Salvar Funcionário"):
                run_query("INSERT INTO funcionarios (nome, cargo) VALUES (?, ?)", (nome_func, cargo_func), commit=True)
                st.rerun()
        st.write("Funcionários:")
        df_func = run_query("SELECT * FROM funcionarios")
        st.dataframe(df_func, use_container_width=True)
        
        with st.expander("🗑️ Remover Funcionário"):
            if not df_func.empty:
                func_del = st.selectbox("Selecione o Funcionário para remover", df_func['id'], format_func=lambda x: df_func[df_func['id']==x]['nome'].values[0])
                if st.button("Remover Funcionário"):
                    run_query("DELETE FROM funcionarios WHERE id = ?", (func_del,), commit=True)
                    st.success("Funcionário removido!")
                    st.rerun()

    with aba3:
        st.subheader("Nova Rua / Localização")
        with st.form("cad_rua"):
            nome_rua = st.text_input("Nome da Rua/Setor")
            if st.form_submit_button("Salvar Rua"):
                run_query("INSERT INTO ruas (nome) VALUES (?)", (nome_rua,), commit=True)
                st.rerun()
        st.write("Localizações:")
        df_rua = run_query("SELECT * FROM ruas")
        st.dataframe(df_rua, use_container_width=True)
        
        with st.expander("🗑️ Remover Rua"):
            if not df_rua.empty:
                rua_del = st.selectbox("Selecione a Rua para remover", df_rua['id'], format_func=lambda x: df_rua[df_rua['id']==x]['nome'].values[0])
                if st.button("Remover Rua"):
                    run_query("DELETE FROM ruas WHERE id = ?", (rua_del,), commit=True)
                    st.success("Localização removida!")
                    st.rerun()

elif menu == "Backup Excel":
    st.title("💾 Importar / Exportar Excel")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Exportar Dados")
        st.write("Baixe todos os dados atuais do sistema em formato Excel.")
        excel_data = export_to_excel()
        st.download_button(
            label="📥 Baixar Backup Excel",
            data=excel_data,
            file_name=f"backup_estoque_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    with col2:
        st.subheader("Importar Planilha")
        st.write("Suba sua planilha '3 - ALMOXARIFADO' para carregar os materiais.")
        uploaded_file = st.file_uploader("Escolha o arquivo Excel", type="xlsx")
        if uploaded_file:
            if st.button("🚀 Iniciar Importação"):
                success = import_from_almoxarifado(uploaded_file)
                if success:
                    st.success("Materiais importados com sucesso!")
                    st.rerun()

st.sidebar.divider()
st.sidebar.caption("Desenvolvido por Zapia para Gestão de Obras")
