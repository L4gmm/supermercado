import os
import streamlit as st
import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

st.set_page_config(page_title="Supermercado", page_icon="🛒")
load_dotenv()
CAMINHO_CREDENCIAL = os.getenv("FIREBASE_CREDENTIALS_PATH")

@st.cache_resource
def conectar_firebase(caminho_credencial):
    if not firebase_admin._apps:
        cred = credentials.Certificate(caminho_credencial)
        firebase_admin.initialize_app(cred)
    return firestore.client()

if not CAMINHO_CREDENCIAL:
    st.error("Erro: Variável FIREBASE_CREDENTIALS_PATH não configurada no arquivo .env.")
    st.stop()

try:
    db = conectar_firebase(CAMINHO_CREDENCIAL)
except Exception as e:
    st.error(f"Erro ao conectar com o Firebase: {e}")
    st.stop()

st.title("🛒 Supermercado")
st.caption("Conectado ao Firestore do Firebase")

# Adicionamos a aba "Registrar Compra"
aba_funcionarios, aba_clientes, aba_cadastro, aba_lista, aba_compra, aba_consulta = st.tabs(
    ["🧑‍💼 Funcionários", "🛒 Clientes", "➕ Cadastrar", "📋 Produtos", "🛍️ Registrar Compra", "🔎 Consulta"]
)

# FUNCIONÁRIOS
with aba_funcionarios:
    with st.form("form_funcionario", clear_on_submit=True):
        nome = st.text_input("Nome do funcionário")
        idade = st.number_input("Idade", min_value=18, max_value=120, step=1)

        if st.form_submit_button("Cadastrar"):
            if nome.strip():
                db.collection("Funcionarios").add({"nome": nome.strip(), "idade": int(idade)})
                st.success(f"Funcionário '{nome}' cadastrado!")
            else:
                st.warning("Informe o nome.")

# CLIENTES
with aba_clientes:
    with st.form("form_cliente", clear_on_submit=True):
        nome = st.text_input("Nome do cliente")
        idade = st.number_input("Idade", min_value=0, max_value=120, step=1)

        if st.form_submit_button("Cadastrar"):
            if nome.strip():
                db.collection("Clientes").add({"nome": nome.strip(), "idade": int(idade)})
                st.success(f"Cliente '{nome}' cadastrado!")
            else:
                st.warning("Informe o nome.")

# CADASTRO DE PRODUTOS
with aba_cadastro:
    with st.form("form_produto", clear_on_submit=True):
        nome = st.text_input("Nome do produto")
        valor = st.number_input("Preço (R$)", min_value=0.0, max_value=1000000.0, step=0.01, format="%.2f")

        if st.form_submit_button("Cadastrar"):
            if nome.strip():
                db.collection("produtos").add({"nome": nome.strip(), "valor": float(valor)})
                st.success(f"Produto '{nome}' cadastrado!")
            else:
                st.warning("Informe o nome do produto.")

# LISTA DE PRODUTOS
with aba_lista:
    if st.button("🔄 Atualizar lista"):
        st.rerun()

    produtos = [{"id": d.id, **d.to_dict()} for d in db.collection("produtos").stream()]

    if not produtos:
        st.info("Nenhum produto cadastrado.")

    for produto in produtos:
        col1, col2, col3, col4 = st.columns([4, 3, 1, 1])
        col1.write(f"{produto.get('nome', '—')}")
        
        preco = produto.get('valor', 0)
        col2.write(f"R$ {preco:.2f}" if isinstance(preco, (int, float)) else "—")

        if col4.button("🗑️", key=produto["id"]):
            db.collection("produtos").document(produto["id"]).delete()
            st.rerun()

# REGISTRAR COMPRA (NOVA ABA)
with aba_compra:
    st.subheader("🛍️ Caixa do Supermercado")

    # Busca clientes e produtos salvos no banco para selecionar
    clientes_docs = list(db.collection("Clientes").stream())
    produtos_docs = list(db.collection("produtos").stream())

    clientes_dict = {c.to_dict().get("nome"): c.id for c in clientes_docs}
    produtos_dict = {p.to_dict().get("nome"): p.to_dict() for p in produtos_docs}

    if not clientes_dict:
        st.warning("Cadastre pelo menos um cliente na aba 'Clientes' primeiro.")
    elif not produtos_dict:
        st.warning("Cadastre pelo menos um produto na aba 'Cadastrar' primeiro.")
    else:
        with st.form("form_compra"):
            cliente_selecionado = st.selectbox("Selecione o Cliente", options=list(clientes_dict.keys()))
            
            # Caixa de seleção múltipla para escolher vários produtos de uma vez
            produtos_selecionados = st.multiselect(
                "Selecione os produtos que deseja comprar:", 
                options=list(produtos_dict.keys())
            )

            # Calcula o valor total com base nos produtos escolhidos
            valor_total = sum([produtos_dict[p]["valor"] for p in produtos_selecionados])
            
            if produtos_selecionados:
                st.info(f"*Valor Total da Compra:* R$ {valor_total:.2f}")

            if st.form_submit_button("Finalizar Compra"):
                if produtos_selecionados:
                    # Salva a compra no Firestore na coleção "Compras"
                    dados_compra = {
                        "cliente": cliente_selecionado,
                        "produtos": produtos_selecionados,
                        "valor_total": float(valor_total)
                    }
                    db.collection("Compras").add(dados_compra)
                    st.success(f"Compra para {cliente_selecionado} finalizada com sucesso! Total: R$ {valor_total:.2f}")
                else:
                    st.warning("Selecione ao menos um produto para realizar a compra.")

    st.divider()
    st.subheader("📋 Histórico de Compras Realizadas")
    
    compras = [d.to_dict() for d in db.collection("Compras").stream()]
    if not compras:
        st.info("Nenhuma compra registrada ainda.")
    else:
        for compra in compras:
            produtos_str = ", ".join(compra.get("produtos", []))
            st.write(f"🛒 *Cliente:* {compra.get('cliente')} | *Produtos:* {produtos_str} | *Total:* R$ {compra.get('valor_total', 0):.2f}")

# CONSULTA (Funcionários e Clientes)
with aba_consulta:
    st.subheader("🧑‍💼 Funcionários")

    funcionarios = [{"id": d.id, **d.to_dict()} for d in db.collection("Funcionarios").stream()]

    if not funcionarios:
        st.info("Nenhum funcionário cadastrado.")

    for funcionario in funcionarios:
        col1, col2, col3 = st.columns([4, 3, 1])
        col1.write(f"{funcionario.get('nome', '—')}")
        col2.write(f"{funcionario.get('idade', '—')} anos")

    st.divider()

    st.subheader("🛒 Clientes")

    clientes = [{"id": d.id, **d.to_dict()} for d in db.collection("Clientes").stream()]

    if not clientes:
        st.info("Nenhum cliente cadastrado.")

    for cliente in clientes:
        col1, col2, col3 = st.columns([4, 3, 1])
        col1.write(f"{cliente.get('nome', '—')}")
        col2.write(f"{cliente.get('idade', '—')} anos")