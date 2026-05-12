import streamlit as st
import os
import json
from google import genai
from google.genai import types, errors
from dotenv import load_dotenv
import plotly.express as px
from datetime import datetime

# Importando os módulos do projeto modularizado
from database import DatabaseManager
from services import (
    gerar_pdf,
    obter_prompt,
    obter_prompt_gupy,
    obter_prompt_followup,
    clean_ai_response,
    extrair_texto_url,
    obter_prompt_extrair_vaga,
)

# 1. SETUP, SEGURANÇA E AMBIENTE
load_dotenv(override=True)
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ Erro Crítico: GOOGLE_API_KEY não encontrada no arquivo .env")
    st.stop()

cliente = genai.Client(api_key=API_KEY)
db = DatabaseManager()

# Função auxiliar para chamadas à API com fallback entre modelos
def call_gemini_with_fallback(func, *args, **kwargs):
    """
    Tenta chamar a API do Gemini com fallback automático entre modelos
    caso ocorra erro de cota (429) ou indisponibilidade (503).
    Usa gemini-2.5-flash como principal (gratuito, limites altos).
    Cada modelo é tentado até 2 vezes antes de pular para o próximo.
    """
    import time
    
    # Modelos em ordem de preferência — expandido com novos modelos disponíveis
    modelos_fallback = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash-lite",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite-preview",
    ]
    
    MAX_RETRIES_PER_MODEL = 2  # Tentativas por modelo antes de pular
    last_exception = None
    last_was_quota = False
    
    for i, modelo in enumerate(modelos_fallback):
        for attempt in range(MAX_RETRIES_PER_MODEL):
            try:
                kwargs['model'] = modelo
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                erro_str = str(e)
                is_quota_error = "429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str
                is_unavailable = "503" in erro_str or "UNAVAILABLE" in erro_str
                is_retryable = is_quota_error or is_unavailable
                last_was_quota = is_quota_error
                
                if not is_retryable:
                    # Erro não-retryable (ex: permissão, formato inválido) — propaga
                    raise e
                
                # Se ainda tem retries neste modelo, espera e tenta de novo
                if attempt < MAX_RETRIES_PER_MODEL - 1:
                    wait_secs = 8 if is_unavailable else 5
                    st.info(
                        f"⏳ Modelo `{modelo}` {('indisponível' if is_unavailable else 'cota atingida')}. "
                        f"Retentando em {wait_secs}s... (tentativa {attempt + 2}/{MAX_RETRIES_PER_MODEL})"
                    )
                    time.sleep(wait_secs)
                    continue
                
                # Esgotou retries deste modelo — tenta o próximo
                if i < len(modelos_fallback) - 1:
                    motivo = "cota excedida" if is_quota_error else "temporariamente indisponível"
                    st.warning(
                        f"⚠️ Modelo `{modelo}` {motivo}. "
                        f"Tentando modelo alternativo `{modelos_fallback[i+1]}`..."
                    )
                    wait_secs = 10 if is_unavailable else 5
                    time.sleep(wait_secs)
                    break  # Sai do loop de retries, vai para o próximo modelo
    
    # Todos os modelos e retries falharam
    if last_was_quota:
        raise Exception(
            "🚫 Todos os modelos estão com cota excedida. "
            "Aguarde 1-2 minutos e tente novamente. "
            "Isso acontece por excesso de requisições, não por problema na API Key."
        ) from last_exception
    else:
        raise Exception(
            "🚫 Todos os modelos estão temporariamente indisponíveis "
            "por alta demanda no Google. Aguarde 1-2 minutos e tente novamente. "
            "Isso é um problema temporário do lado do Google, não da sua API Key."
        ) from last_exception

# Configuração da Interface
st.set_page_config(page_title="Curriculator v5.0", layout="wide")

# ═══════════════════════════════════════════════════════════
# CSS CUSTOMIZADO — TEMA PREMIUM
# ═══════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1a3a5a 0%, #0d253a 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-3px); }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 5px 0;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 0.85rem;
        opacity: 0.85;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-delta {
        font-size: 0.8rem;
        margin-top: 5px;
        padding: 2px 8px;
        border-radius: 10px;
        display: inline-block;
    }
    .delta-up {
        background: rgba(46, 204, 113, 0.25);
        color: #2ecc71;
    }
    .delta-down {
        background: rgba(231, 76, 60, 0.25);
        color: #e74c3c;
    }
    .delta-neutral {
        background: rgba(255, 255, 255, 0.15);
        color: #bbb;
    }

    /* Header */
    .app-header {
        background: linear-gradient(135deg, #1a3a5a 0%, #2c5f8a 100%);
        padding: 25px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        color: white;
    }
    .app-header h1 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
    }
    .app-header p {
        margin: 5px 0 0;
        opacity: 0.8;
        font-size: 0.95rem;
    }

    /* Alerta cards */
    .alert-card {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
        border-radius: 10px;
        padding: 12px 16px;
        color: white;
        margin-bottom: 8px;
        font-size: 0.85rem;
    }
    .alert-card strong { font-size: 0.95rem; }

    /* Section headers */
    .section-header {
        color: #1a3a5a;
        font-size: 1.1rem;
        font-weight: 600;
        border-left: 4px solid #1a3a5a;
        padding-left: 12px;
        margin: 20px 0 10px;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div class="app-header">
        <h1>🤖 Curriculator Exterminador de Negativas</h1>
        <p>Dashboard inteligente de gestão de candidaturas</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# Configuração do Currículo Mestre (Sidebar)
st.sidebar.markdown(
    '<div class="section-header">📄 Seu Currículo Mestre</div>',
    unsafe_allow_html=True,
)
file_cv = st.sidebar.file_uploader(
    "Upload do seu LinkedIn PDF ou Currículo base",
    type=["pdf"],
    help="Este arquivo será usado pela IA para adaptar sua experiência.",
)

# Diagnóstico de API Key (Mascarada)
if API_KEY:
    masked_key = f"{API_KEY[:6]}...{API_KEY[-4:]}"
    st.sidebar.caption(f"🔑 API Key ativa: `{masked_key}`")
else:
    st.sidebar.error("❌ API Key não detectada.")

# Cache do upload do PDF
@st.cache_resource
def upload_cv_cached(uploaded_file):
    """Faz upload do arquivo para o Gemini uma única vez e retorna o objeto."""
    if uploaded_file is None:
        return None
    
    # Salvar temporariamente para fazer o upload via SDK
    os.makedirs("temp", exist_ok=True)
    temp_path = os.path.join("temp", uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    file_gemini = cliente.files.upload(file=temp_path)
    
    # Limpeza opcional do arquivo temporário
    # os.remove(temp_path)
    
    return file_gemini


# ═══════════════════════════════════════════════════════════
# HELPER: Renderizar KPI Card
# ═══════════════════════════════════════════════════════════
def render_kpi(label, value, delta=None, icon="📊"):
    delta_html = ""
    if delta is not None:
        if delta > 0:
            delta_html = (
                f'<div class="kpi-delta delta-up">▲ +{delta} esta semana</div>'
            )
        elif delta < 0:
            delta_html = (
                '<div class="kpi-delta delta-down">'
                f"▼ {delta} esta semana</div>"
            )
        else:
            delta_html = (
                '<div class="kpi-delta delta-neutral">— sem variação</div>'
            )
    st.markdown(
        f"""
        <div class="kpi-card">
            <div style="font-size: 1.5rem;">{icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════
# DADOS GLOBAIS
# ═══════════════════════════════════════════════════════════
df = db.get_df()
stats_atual = db.get_stats_semana(0)
stats_anterior = db.get_stats_semana(1)

# ═══════════════════════════════════════════════════════════
# LAYOUT COM ABAS
# ═══════════════════════════════════════════════════════════
tab_dashboard, tab_candidatura, tab_gestao = st.tabs(
    ["📊 Dashboard", "📝 Nova Candidatura", "🛠️ Gestão"]
)

# ─────────────────────────────────────────────────────────
# ABA 1: DASHBOARD
# ─────────────────────────────────────────────────────────
with tab_dashboard:

    if df.empty:
        st.info(
            "📭 Nenhuma candidatura registrada ainda. "
            "Vá para a aba **Nova Candidatura** para começar!"
        )
    else:
        # KPIs
        total_enviado = len(df)
        entrevistas = len(df[df["status"] == "Entrevista"])
        reprovados = len(df[df["status"] == "Reprovado"])
        taxa_conversao = (
            round(entrevistas / total_enviado * 100, 1)
            if total_enviado > 0
            else 0
        )

        # Deltas semanais
        delta_total = stats_atual["total"] - stats_anterior["total"]
        delta_entrevistas = (
            stats_atual["entrevistas"] - stats_anterior["entrevistas"]
        )

        # Dias médio sem resposta
        df_enviados = df[df["status"].str.contains("Enviado", na=False)]
        if not df_enviados.empty:
            dias_list = [
                (datetime.now() - datetime.strptime(d, "%Y-%m-%d")).days
                for d in df_enviados["data"]
            ]
            dias_medio = round(sum(dias_list) / len(dias_list), 1)
        else:
            dias_medio = 0

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            render_kpi(
                "Total Enviado", total_enviado,
                delta=delta_total, icon="📤"
            )
        with k2:
            render_kpi(
                "Entrevistas", entrevistas,
                delta=delta_entrevistas, icon="🎯"
            )
        with k3:
            render_kpi(
                "Taxa Conversão", f"{taxa_conversao}%",
                icon="📈"
            )
        with k4:
            render_kpi(
                "Dias Médio s/ Resposta", f"{dias_medio}d",
                icon="⏳"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráficos lado a lado
        col_funnel, col_channel = st.columns(2)

        with col_funnel:
            st.markdown(
                '<div class="section-header">Funil de Conversão</div>',
                unsafe_allow_html=True,
            )
            status_order = [
                "Enviado", "Sem Resposta", "Follow-up Enviado",
                "Entrevista", "Teste", "Contratado"
            ]
            funnel_data = []
            for s in status_order:
                count = len(
                    df[df["status"].str.contains(s, na=False)]
                )
                if count > 0:
                    funnel_data.append({"Etapa": s, "Quantidade": count})

            if funnel_data:
                import pandas as pd
                df_funnel = pd.DataFrame(funnel_data)
                fig_funnel = px.funnel(
                    df_funnel,
                    x="Quantidade",
                    y="Etapa",
                    color_discrete_sequence=["#1a3a5a"],
                )
                fig_funnel.update_layout(
                    height=350,
                    margin=dict(l=0, r=0, t=10, b=0),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12),
                )
                st.plotly_chart(fig_funnel, use_container_width=True)

        with col_channel:
            st.markdown(
                '<div class="section-header">Distribuição por Canal</div>',
                unsafe_allow_html=True,
            )
            canal_counts = (
                df["status"]
                .apply(
                    lambda x: (
                        "Gupy"
                        if "Gupy" in str(x)
                        else (
                            "E-mail"
                            if "E-mail" in str(x)
                            else (
                                "Currículo"
                                if "Currículo" in str(x)
                                else "Outro"
                            )
                        )
                    )
                )
                .value_counts()
                .reset_index()
            )
            canal_counts.columns = ["Canal", "Quantidade"]
            fig_pie = px.pie(
                canal_counts,
                values="Quantidade",
                names="Canal",
                color_discrete_sequence=[
                    "#1a3a5a", "#2c5f8a", "#3d7ab5", "#f39c12"
                ],
                hole=0.4,
            )
            fig_pie.update_layout(
                height=350,
                margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(size=12),
            )
            fig_pie.update_traces(
                textposition="inside", textinfo="value+label"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Volume diário
        st.markdown(
            '<div class="section-header">Volume Diário de Candidaturas</div>',
            unsafe_allow_html=True,
        )
        df_c = df["data"].value_counts().reset_index()
        df_c.columns = ["data", "candidaturas"]
        fig_bar = px.bar(
            df_c.sort_values("data"),
            x="data",
            y="candidaturas",
            color_discrete_sequence=["#1a3a5a"],
        )
        fig_bar.update_layout(
            xaxis_type="category",
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="",
            yaxis_title="Candidaturas",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Alertas de Follow-up
        df_followup = db.get_pendentes_followup(dias=7)
        if not df_followup.empty:
            st.markdown(
                '<div class="section-header">'
                "⏰ Pendentes de Follow-up</div>",
                unsafe_allow_html=True,
            )
            for _, row in df_followup.iterrows():
                dias_passados = (
                    datetime.now()
                    - datetime.strptime(row["data"], "%Y-%m-%d")
                ).days
                st.markdown(
                    f"""
                    <div class="alert-card">
                        <strong>📌 {row['empresa']}</strong>
                        — {row['cargo']} • {dias_passados} dias sem resposta
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                col_fu1, col_fu2 = st.columns([1, 1])
                with col_fu1:
                    if st.button(
                        "✉️ Gerar Follow-up",
                        key=f"followup_{row['id']}",
                    ):
                        with st.spinner("Gerando e-mail de follow-up..."):
                            prompt_fu = obter_prompt_followup(
                                row["empresa"],
                                row["cargo"],
                                dias_passados,
                            )
                            try:
                                resp_fu = call_gemini_with_fallback(
                                    cliente.models.generate_content,
                                    model="gemini-2.5-flash",
                                    contents=[prompt_fu],
                                )
                                texto_fu = clean_ai_response(resp_fu.text)
                                st.text_area(
                                    "E-mail de Follow-up:",
                                    value=texto_fu,
                                    height=200,
                                    key=f"fu_text_{row['id']}",
                                )
                            except Exception as e:
                                # O erro 429 agora é tratado dentro do call_gemini_with_fallback
                                # mas deixamos o catch aqui para outros erros críticos.
                                st.error(f"❌ Erro ao gerar follow-up: {e}")
                with col_fu2:
                    if st.button(
                        "✅ Marcar Follow-up Enviado",
                        key=f"mark_fu_{row['id']}",
                    ):
                        db.update_status(
                            row["id"], "Follow-up Enviado"
                        )
                        st.rerun()

        # Skills Ranking
        df_skills = db.get_skills_ranking()
        if not df_skills.empty:
            st.markdown(
                '<div class="section-header">'
                "🎯 Skills Mais Pedidas pelo Mercado</div>",
                unsafe_allow_html=True,
            )
            top_skills = df_skills.head(15)
            fig_skills = px.bar(
                top_skills.iloc[::-1],
                x="Frequência",
                y="Skill",
                orientation="h",
                color_discrete_sequence=["#1a3a5a"],
            )
            fig_skills.update_layout(
                height=400,
                margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis_title="",
                xaxis_title="Vezes pedida",
            )
            st.plotly_chart(
                fig_skills, use_container_width=True
            )

    # Exportar Excel na sidebar
    if not df.empty:
        if st.sidebar.button("📊 Exportar Relatório Excel"):
            df.to_excel(
                "controle_dados/Relatorio_Exportado.xlsx",
                index=False,
            )
            st.sidebar.success("✅ Excel gerado com sucesso!")


# ─────────────────────────────────────────────────────────
# ABA 2: NOVA CANDIDATURA
# ─────────────────────────────────────────────────────────
with tab_candidatura:

    st.markdown(
        '<div class="section-header">'
        'Preencha os dados da vaga</div>',
        unsafe_allow_html=True,
    )

    # --- Auto-fill via URL ---
    col_url, col_btn = st.columns([4, 1])
    url_vaga = col_url.text_input(
        "🔗 URL da Vaga (opcional)",
        placeholder="Cole o link da vaga aqui...",
    )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        buscar_url = st.button("🔍 Buscar")

    # Inicializar session_state para campos editáveis
    state_keys = [
        "af_empresa", "af_cargo", "af_descricao",
        "af_requisitos", "af_beneficios",
    ]
    for key in state_keys:
        if key not in st.session_state:
            st.session_state[key] = ""

    if buscar_url and url_vaga:
        with st.spinner(
            "🌐 Extraindo dados da vaga..."
        ):
            try:
                texto_pag = extrair_texto_url(url_vaga)
                prompt_ext = obter_prompt_extrair_vaga(
                    texto_pag
                )
                resp_ext = call_gemini_with_fallback(
                    cliente.models.generate_content,
                    model="gemini-2.5-flash",
                    contents=[prompt_ext],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )
                raw = resp_ext.text.strip()
                if "```json" in raw:
                    raw = (
                        raw.split("```json")[1]
                        .split("```")[0]
                        .strip()
                    )
                elif "```" in raw:
                    raw = (
                        raw.split("```")[1]
                        .split("```")[0]
                        .strip()
                    )
                dados_url = json.loads(raw)
                st.session_state["af_empresa"] = (
                    dados_url.get("empresa", "")
                )
                st.session_state["af_cargo"] = (
                    dados_url.get("cargo", "")
                )
                st.session_state["af_descricao"] = (
                    dados_url.get("descricao", "")
                )
                # Requisitos e benefícios como JSON
                reqs = dados_url.get("requisitos", [])
                bens = dados_url.get("beneficios", [])
                st.session_state["af_requisitos"] = (
                    json.dumps(reqs, ensure_ascii=False)
                    if isinstance(reqs, list) else str(reqs)
                )
                st.session_state["af_beneficios"] = (
                    json.dumps(bens, ensure_ascii=False)
                    if isinstance(bens, list) else str(bens)
                )
                st.success(
                    "✅ Dados extraídos! Verifique abaixo."
                )
            except Exception as err:
                if "429" in str(err) or "RESOURCE_EXHAUSTED" in str(err):
                    st.error("⚠️ Limite de cota atingido (429)! O Gemini está sob alta carga. Por favor, aguarde cerca de 60 segundos e clique em 'Buscar' novamente.")
                else:
                    st.error(f"❌ Erro ao buscar URL: {err}")

    col1, col2 = st.columns(2)
    empresa = col1.text_input(
        "Nome da Empresa",
        value=st.session_state["af_empresa"],
    )
    cargo = col2.text_input(
        "Cargo Desejado",
        value=st.session_state["af_cargo"],
    )
    texto_vaga = st.text_area(
        "Descrição da Vaga",
        value=st.session_state["af_descricao"],
        height=150,
    )

    # Mostrar requisitos e benefícios extraídos
    col_req, col_ben = st.columns(2)
    with col_req:
        with st.expander("📋 Requisitos da Vaga", expanded=bool(
            st.session_state["af_requisitos"]
        )):
            requisitos_edit = st.text_area(
                "Skills e conhecimentos pedidos:",
                value=st.session_state["af_requisitos"],
                height=120,
                key="edit_requisitos",
                help="JSON lista. Ex: [\"Python\", \"SQL\"]",
            )
    with col_ben:
        with st.expander("🎁 Benefícios", expanded=bool(
            st.session_state["af_beneficios"]
        )):
            beneficios_edit = st.text_area(
                "Benefícios oferecidos:",
                value=st.session_state["af_beneficios"],
                height=120,
                key="edit_beneficios",
                help="JSON lista. Ex: [\"VR\", \"Plano\"]",
            )

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
            # Detecção de duplicatas
            if db.check_duplicata(empresa, cargo):
                st.warning(
                    f"⚠️ Já existe uma candidatura para **{cargo}** "
                    f"na **{empresa}**. Processando mesmo assim..."
                )

            if "Gupy" in canal:
                with st.status(
                    "🧠 Curriculator em execução...", expanded=True
                ) as status_ui:
                    try:
                        if not file_cv:
                            st.error("⚠️ Por favor, faça o upload do seu currículo na barra lateral antes de processar.")
                            st.stop()
                            
                        status_ui.write("📤 Analisando currículo...")
                        arquivo_cv = upload_cv_cached(file_cv)

                        prompt_gupy = obter_prompt_gupy("", texto_vaga)

                        status_ui.write("⚙️ Consultando Gemini...")
                        resposta = call_gemini_with_fallback(
                            cliente.models.generate_content,
                            model="gemini-2.5-flash",
                            contents=[arquivo_cv, prompt_gupy],
                        )

                        status_reg = f"Enviado ({canal})"
                        texto_limpo = clean_ai_response(resposta.text)

                        st.subheader("✨ Texto para Gupy:")
                        st.text_area(
                            "Copie:", value=texto_limpo, height=300
                        )

                        db.add_candidatura(
                            empresa, cargo, status_reg, "N/A",
                            texto_gerado=texto_limpo,
                            requisitos=requisitos_edit,
                            beneficios=beneficios_edit,
                        )

                        status_ui.update(
                            label="✅ Pipeline Concluído!",
                            state="complete",
                        )

                        if st.button(
                            "🔄 Finalizar e Atualizar Dashboard"
                        ):
                            st.rerun()

                    except Exception as err:
                        st.error(f"❌ Erro no processamento: {err}")

            else:
                with st.status(
                    "🧠 Curriculator em execução...", expanded=True
                ) as status_ui:
                    try:
                        if not file_cv:
                            st.error("⚠️ Por favor, faça o upload do seu currículo na barra lateral antes de processar.")
                            st.stop()

                        status_ui.write("📤 Analisando currículo...")
                        arquivo_cv = upload_cv_cached(file_cv)

                        prompt = obter_prompt(canal, empresa, cargo)

                        status_ui.write("⚙️ Consultando Gemini...")
                        resposta = call_gemini_with_fallback(
                            cliente.models.generate_content,
                            model="gemini-2.5-flash",
                            contents=[arquivo_cv, prompt, texto_vaga],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                            ),
                        )

                        status_reg = f"Enviado ({canal})"
                        path_pdf = "N/A"
                        texto_salvar = ""

                        status_ui.write(
                            "🎨 Tratando dados e "
                            "gerando modelo SempreIT..."
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
                            st.text_input(
                                "📬 Destinatário:",
                                value=dados_json.get(
                                    "email_destinatario", ""
                                ),
                            )
                            st.text_input(
                                "📌 Assunto:",
                                value=dados_json.get(
                                    "email_assunto", ""
                                ),
                            )
                            st.text_area(
                                "✉️ Corpo do E-mail (copie):",
                                value=dados_json.get(
                                    "email_corpo", ""
                                ),
                                height=200,
                            )
                            texto_salvar = dados_json.get(
                                "email_corpo", ""
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

                        db.add_candidatura(
                            empresa, cargo, status_reg, path_pdf,
                            texto_gerado=texto_salvar,
                            requisitos=requisitos_edit,
                            beneficios=beneficios_edit,
                        )
                        status_ui.update(
                            label="✅ Pipeline Concluído!",
                            state="complete",
                        )

                        if st.button(
                            "🔄 Finalizar e Atualizar Dashboard"
                        ):
                            st.rerun()

                    except Exception as err:
                        st.error(f"❌ Erro no processamento: {err}")


# ─────────────────────────────────────────────────────────
# ABA 3: GESTÃO
# ─────────────────────────────────────────────────────────
with tab_gestao:

    if df.empty:
        st.info(
            "📭 Nenhum registro encontrado. "
            "Comece criando candidaturas na aba anterior."
        )
    else:
        st.markdown(
            '<div class="section-header">'
            'Gerenciar Registros</div>',
            unsafe_allow_html=True,
        )

        col_manage, col_status = st.columns([1, 1])

        with col_manage:
            df["Display"] = (
                df["id"].astype(str) + " - "
                + df["empresa"]
                + " (" + df["cargo"] + ")"
            )
            selecao = st.selectbox(
                "Selecione um registro:",
                df["Display"].tolist(),
            )
            id_sel = int(selecao.split(" - ")[0])

            c1, c2 = st.columns(2)
            if c1.button("❌ EXCLUIR"):
                db.delete_reg(id_sel)
                st.rerun()

        with col_status:
            status_options = [
                "Enviado",
                "Sem Resposta",
                "Follow-up Enviado",
                "Entrevista",
                "Teste",
                "Reprovado",
                "Contratado",
            ]
            novo_st = st.selectbox(
                "Atualizar Status:", status_options
            )
            if st.button("✅ SALVAR STATUS"):
                db.update_status(id_sel, novo_st)
                st.rerun()

        # Comentários / Feedback
        st.markdown(
            '<div class="section-header">'
            '💬 Comentários e Feedback</div>',
            unsafe_allow_html=True,
        )
        reg_sel = df[df["id"] == id_sel].iloc[0]
        comentario_atual = reg_sel.get(
            "comentarios", ""
        ) or ""
        novo_comentario = st.text_area(
            f"Notas sobre {reg_sel['empresa']} "
            f"- {reg_sel['cargo']}:",
            value=comentario_atual,
            height=100,
            placeholder=(
                "Ex: Recruiter pediu entrevista, "
                "teste técnico marcado, etc."
            ),
        )
        if st.button("💾 SALVAR COMENTÁRIO"):
            db.update_comentario(id_sel, novo_comentario)
            st.success("✅ Comentário salvo!")
            st.rerun()

        # Detalhes da vaga selecionada
        with st.expander(
            "📋 Detalhes da Candidatura Selecionada"
        ):
            c_req, c_ben = st.columns(2)
            with c_req:
                reqs_raw = reg_sel.get(
                    "requisitos", ""
                ) or ""
                st.markdown("**📋 Requisitos:**")
                try:
                    reqs_list = json.loads(reqs_raw)
                    if isinstance(reqs_list, list):
                        for r in reqs_list:
                            st.markdown(f"- {r}")
                    else:
                        st.text(reqs_raw)
                except (json.JSONDecodeError, TypeError):
                    st.text(
                        reqs_raw if reqs_raw
                        else "Sem dados"
                    )
            with c_ben:
                bens_raw = reg_sel.get(
                    "beneficios", ""
                ) or ""
                st.markdown("**🎁 Benefícios:**")
                try:
                    bens_list = json.loads(bens_raw)
                    if isinstance(bens_list, list):
                        for b in bens_list:
                            st.markdown(f"- {b}")
                    else:
                        st.text(bens_raw)
                except (json.JSONDecodeError, TypeError):
                    st.text(
                        bens_raw if bens_raw
                        else "Sem dados"
                    )

        st.markdown(
            '<div class="section-header">'
            '📋 Histórico Completo</div>',
            unsafe_allow_html=True,
        )
        cols_hide = ["Display"]
        df_display = df.drop(
            columns=cols_hide, errors="ignore"
        ).iloc[::-1]
        st.dataframe(
            df_display,
            use_container_width=True,
            height=400,
        )
