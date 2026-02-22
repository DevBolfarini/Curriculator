import streamlit as st
import os
import json
from google import genai
from dotenv import load_dotenv
import plotly.express as px

# Importando os módulos do projeto modularizado
from database import DatabaseManager
from services import gerar_pdf, obter_prompt

# 1. SETUP, SEGURANÇA E AMBIENTE
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ Erro Crítico: GOOGLE_API_KEY não encontrada no arquivo .env")
    st.stop()

cliente = genai.Client(api_key=API_KEY)
db = DatabaseManager()

# Configuração da Interface
st.set_page_config(page_title="Curriculator v4.2.3", layout="wide")
st.title("🤖 Curriculator Exterminador de Negativas")

# 2. DASHBOARD DE PERFORMANCE (KPIs)
df = db.get_df()
if not df.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Enviado", len(df))
    gupy_count = len(df[df['status'].str.contains("Gupy", na=False)])
    m2.metric("Vagas Gupy", gupy_count)
    m3.metric("Entrevistas", len(df[df['status'] == 'Entrevista']))

    if st.sidebar.button("📊 Exportar Relatório Excel"):
        df.to_excel("controle_dados/Relatorio_Exportado.xlsx", index=False)
        st.sidebar.success("✅ Excel gerado com sucesso!")
    st.divider()

# 3. INTERFACE DE ENTRADA E PROCESSAMENTO
with st.expander("📝 Nova Candidatura", expanded=True):
    col1, col2 = st.columns(2)
    empresa = col1.text_input("Nome da Empresa")
    cargo = col2.text_input("Cargo Desejado")
    texto_vaga = st.text_area("Descrição da Vaga", height=150)
    canal = st.radio(
        "Canal de Envio:",
        [
            "Gupy (Apresente-se)",
            "E-mail (PDF + Texto)",
            "Currículo (Apenas PDF)",
        ],
        horizontal=True,
    )

    if st.button("🚀 Processar Inteligência"):
        if not empresa or not cargo or not texto_vaga:
            st.warning("Preencha todos os campos obrigatórios.")
        else:
            with st.status(
                "🧠 Curriculator em execução...",
                expanded=True
            ) as status_ui:
                try:
                    status_ui.write("📤 Analisando linkedin.pdf...")
                    arquivo_cv = cliente.files.upload(file="linkedin.pdf")

                    prompt = obter_prompt(canal, empresa, cargo)

                    status_ui.write("⚙️ Consultando Gemini...")
                    resposta = cliente.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[arquivo_cv, prompt, texto_vaga],
                    )

                    status_reg = f"Enviado ({canal})"
                    path_pdf = "N/A"

                    if "Gupy" in canal:
                        st.subheader("✨ Texto para Gupy:")
                        st.text_area("Copie:", value=resposta.text, height=300)
                    else:
                        status_ui.write(
                            "🎨 Tratando dados e gerando modelo SempreIT..."
                        )

                        conteudo_bruto = resposta.text.strip()
                        if "```json" in conteudo_bruto:
                            conteudo_limpo = (
                                conteudo_bruto.split("```json")[1]
                                .split("```")[0]
                                .strip()
                            )
                        elif "```" in conteudo_bruto:
                            conteudo_limpo = (
                                conteudo_bruto.split("```")[1]
                                .split("```")[0]
                                .strip()
                            )
                        else:
                            conteudo_limpo = conteudo_bruto

                        dados_json = json.loads(conteudo_limpo)

                        if "E-mail" in canal:
                            st.subheader("📧 Sugestão de E-mail:")
                            st.text_area(
                                "Copie:",
                                value=dados_json.get("email_corpo", ""),
                                height=150,
                            )

                        path_pdf = gerar_pdf(dados_json, empresa)

                        st.success("✅ Currículo gerado com sucesso!")

                        with open(path_pdf, "rb") as f:
                            st.download_button(
                                label="📥 BAIXAR CURRÍCULO AGORA",
                                data=f,
                                file_name=os.path.basename(path_pdf),
                                mime="application/pdf",
                                key="download_btn_final",
                            )

                    # Salva no Banco de Dados
                    db.add_candidatura(empresa, cargo, status_reg, path_pdf)
                    status_ui.update(
                        label="✅ Pipeline Concluído!", state="complete"
                    )

                    # Botão para resetar a tela manualmente,
                    # evitando sumir o download
                    if st.button("🔄 Finalizar e Atualizar Dashboard"):
                        st.rerun()

                except Exception as err:
                    st.error(f"❌ Erro no processamento: {err}")

# 4. GESTÃO DE DADOS (DASHBOARD E CRUD)
if not df.empty:
    col_graph, col_manage = st.columns([2, 1])

    with col_graph:
        st.subheader("📈 Volume Diário")
        df_c = df["data"].value_counts().reset_index()
        df_c.columns = ["data", "candidaturas"]
        fig = px.bar(
            df_c.sort_values("data"),
            x="data",
            y="candidaturas",
            color_discrete_sequence=["#1a3a5a"],
        )
        fig.update_layout(
            xaxis_type="category",
            yaxis_range=[0, 10],
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_manage:
        st.subheader("🛠️ Gestão")
        df["Display"] = df["id"].astype(str) + " - " + df["empresa"]
        selecao = st.selectbox(
            "Selecione um registro:", df["Display"].tolist()
        )
        id_sel = int(selecao.split(" - ")[0])

        c1, c2 = st.columns(2)
        if c1.button("❌ EXCLUIR"):
            db.delete_reg(id_sel)
            st.rerun()

        status_options = [
            "Enviado", "Entrevista", "Teste", "Reprovado", "Contratado"
        ]
        novo_st = st.selectbox("Status:", status_options)
        if st.button("✅ SALVAR"):
            db.update_status(id_sel, novo_st)
            st.rerun()

    st.subheader("📋 Histórico Completo (SQLite)")
    st.dataframe(
        df.drop(columns=["Display"]).iloc[::-1], use_container_width=True
    )
