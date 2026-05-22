import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import io
import time
import re
import json

# ── Configuração da página ─────────────────────────────────────────
st.set_page_config(
    page_title="CV Analyzer AI",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Textos (PT / EN) ───────────────────────────────────────────────
TEXTS = {
    "pt": {
        "title": "📄 CV Analyzer AI",
        "subtitle": "Analise seu currículo com Inteligência Artificial",
        "api_label": "Sua chave da API Gemini",
        "api_help": "Obtenha grátis em aistudio.google.com",
        "api_placeholder": "AIza...",
        "upload_label": "Envie seu currículo (PDF)",
        "upload_help": "Máximo 5 páginas · 5 MB",
        "job_label": "Cole a descrição da vaga",
        "job_placeholder": "Título da vaga, requisitos, responsabilidades...",
        "analyze_btn": "Analisar Currículo",
        "analyzing": "Analisando com IA...",
        "error_api": "⚠️ Chave de API inválida ou sem créditos.",
        "error_pdf": "⚠️ Não foi possível ler o PDF. Verifique o arquivo.",
        "error_pages": "⚠️ PDF com mais de 5 páginas. Envie um currículo mais curto.",
        "error_size": "⚠️ Arquivo muito grande. Máximo 5 MB.",
        "error_empty": "⚠️ O PDF parece estar vazio ou protegido.",
        "error_job": "⚠️ Cole a descrição da vaga antes de analisar.",
        "error_generic": "⚠️ Erro inesperado. Tente novamente.",
        "rate_limit": "⏳ Aguarde {} segundos antes de fazer outra análise.",
        "score_label": "Compatibilidade com a vaga",
        "section_strengths": "✅ Pontos Fortes",
        "section_gaps": "⚠️ Lacunas Identificadas",
        "section_suggestions": "💡 Sugestões de Melhoria",
        "section_keywords": "🔑 Keywords que Faltam",
        "section_summary": "📋 Resumo Geral",
        "pages_info": "✓ {} página(s) lidas",
        "footer": "Feito por Davi Marinho · Gemini API",
    },
    "en": {
        "title": "📄 CV Analyzer AI",
        "subtitle": "Analyze your resume with Artificial Intelligence",
        "api_label": "Your Gemini API Key",
        "api_help": "Get it free at aistudio.google.com",
        "api_placeholder": "AIza...",
        "upload_label": "Upload your resume (PDF)",
        "upload_help": "Max 5 pages · 5 MB",
        "job_label": "Paste the job description",
        "job_placeholder": "Job title, requirements, responsibilities...",
        "analyze_btn": "Analyze Resume",
        "analyzing": "Analyzing with AI...",
        "error_api": "⚠️ Invalid API key or no credits.",
        "error_pdf": "⚠️ Could not read the PDF. Check the file.",
        "error_pages": "⚠️ PDF has more than 5 pages. Please upload a shorter resume.",
        "error_size": "⚠️ File too large. Maximum 5 MB.",
        "error_empty": "⚠️ The PDF seems empty or protected.",
        "error_job": "⚠️ Paste the job description before analyzing.",
        "error_generic": "⚠️ Unexpected error. Please try again.",
        "rate_limit": "⏳ Wait {} seconds before making another analysis.",
        "score_label": "Job compatibility score",
        "section_strengths": "✅ Strengths",
        "section_gaps": "⚠️ Identified Gaps",
        "section_suggestions": "💡 Improvement Suggestions",
        "section_keywords": "🔑 Missing Keywords",
        "section_summary": "📋 General Summary",
        "pages_info": "✓ {} page(s) read",
        "footer": "Built by Davi Marinho · Gemini API",
    },
}

# ── Prompts ────────────────────────────────────────────────────────
PROMPT_PT = """
Você é um especialista em recrutamento e análise de currículos.
Responda SEMPRE em português brasileiro, independente do idioma do currículo ou da vaga.

Analise o currículo abaixo em relação à vaga descrita e responda EXATAMENTE neste formato JSON, sem texto antes ou depois:

{{
  "score": <número de 0 a 100>,
  "strengths": [<lista de 3 a 5 pontos fortes do currículo em relação à vaga, em português>],
  "gaps": [<lista de 2 a 4 lacunas ou pontos fracos identificados, em português>],
  "suggestions": [<lista de 3 a 5 sugestões concretas de melhoria, em português>],
  "missing_keywords": [<lista de 5 a 10 palavras-chave da vaga que não aparecem no currículo, em português ou no idioma original da vaga>],
  "summary": "<parágrafo único com resumo geral da análise, em português>"
}}

CURRÍCULO:
{cv_text}

VAGA:
{job_text}
"""

PROMPT_EN = """
You are an expert in recruitment and resume analysis.
Always respond in English, regardless of the language of the resume or job description.

Analyze the resume below against the job description and respond EXACTLY in this JSON format, with no text before or after:

{{
  "score": <number from 0 to 100>,
  "strengths": [<list of 3 to 5 resume strengths relevant to the job, in English>],
  "gaps": [<list of 2 to 4 identified gaps or weaknesses, in English>],
  "suggestions": [<list of 3 to 5 concrete improvement suggestions, in English>],
  "missing_keywords": [<list of 5 to 10 job keywords missing from the resume, in English>],
  "summary": "<single paragraph with general analysis summary, in English>"
}}

RESUME:
{cv_text}

JOB DESCRIPTION:
{job_text}
"""

# ── Helpers ────────────────────────────────────────────────────────
MAX_PAGES = 5
MAX_SIZE_MB = 5

def extract_pdf_text(file_bytes: bytes) -> tuple[str, int]:
    reader = PdfReader(io.BytesIO(file_bytes))
    num_pages = len(reader.pages)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip(), num_pages

def call_gemini(api_key: str, prompt: str) -> dict:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

def score_color(score: int) -> str:
    if score >= 75: return "#1D9E75"
    if score >= 50: return "#E8A020"
    return "#E24B4A"

def render_score(score: int, label: str):
    color = score_color(score)
    st.markdown(f"""
    <div style="text-align:center;padding:24px 0 8px">
      <div style="font-size:64px;font-weight:700;color:{color};line-height:1">{score}</div>
      <div style="font-size:14px;color:#888;margin-top:4px">{label}</div>
      <div style="background:#eee;border-radius:99px;height:8px;margin:12px auto 0;max-width:280px;overflow:hidden">
        <div style="background:{color};width:{score}%;height:100%;border-radius:99px;transition:width .6s"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_list(items: list):
    for item in items:
        st.markdown(f"- {item}")

# ── Rate limiting ──────────────────────────────────────────────────
RATE_LIMIT_SECONDS = 30

def check_rate_limit() -> tuple[bool, int]:
    last = st.session_state.get("last_analysis_time", 0)
    elapsed = time.time() - last
    if elapsed < RATE_LIMIT_SECONDS:
        return False, int(RATE_LIMIT_SECONDS - elapsed)
    return True, 0

# ── UI ─────────────────────────────────────────────────────────────
def main():
    # seletor de idioma
    col_lang = st.columns([6, 1])
    with col_lang[1]:
        lang = st.selectbox("🌐", ["PT", "EN"], label_visibility="collapsed")

    t = TEXTS["pt"] if lang == "PT" else TEXTS["en"]

    st.markdown(f"## {t['title']}")
    st.markdown(f"<p style='color:#888;margin-top:-12px;margin-bottom:24px'>{t['subtitle']}</p>", unsafe_allow_html=True)

    # ── API Key ────────────────────────────────────────────────────
    saved_key = st.session_state.get("api_key", "")
    with st.expander("🔑 API Key", expanded=not saved_key):
        api_key = st.text_input(
            t["api_label"],
            type="password",
            placeholder=t["api_placeholder"],
            help=f"{t['api_help']} → aistudio.google.com",
            value=saved_key,
        )
        if api_key:
            st.session_state["api_key"] = api_key

    # ── Upload PDF ─────────────────────────────────────────────────
    uploaded = st.file_uploader(
        t["upload_label"],
        type=["pdf"],
        help=t["upload_help"],
    )

    cv_text = ""
    if uploaded:
        file_bytes = uploaded.read()
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > MAX_SIZE_MB:
            st.error(t["error_size"])
        else:
            try:
                cv_text, num_pages = extract_pdf_text(file_bytes)
                if num_pages > MAX_PAGES:
                    st.error(t["error_pages"])
                    cv_text = ""
                elif not cv_text:
                    st.error(t["error_empty"])
                else:
                    st.success(t["pages_info"].format(num_pages))
            except Exception:
                st.error(t["error_pdf"])

    # ── Descrição da vaga ──────────────────────────────────────────
    job_text = st.text_area(
        t["job_label"],
        placeholder=t["job_placeholder"],
        height=160,
    )

    # ── Botão analisar ─────────────────────────────────────────────
    if st.button(t["analyze_btn"], type="primary", use_container_width=True):
        api_key = st.session_state.get("api_key", "").strip()

        if not api_key:
            st.error(t["error_api"])
            st.stop()
        if not cv_text:
            st.error(t["error_pdf"])
            st.stop()
        if not job_text.strip():
            st.error(t["error_job"])
            st.stop()

        ok, wait = check_rate_limit()
        if not ok:
            st.warning(t["rate_limit"].format(wait))
            st.stop()

        with st.spinner(t["analyzing"]):
            try:
                prompt_template = PROMPT_PT if lang == "PT" else PROMPT_EN
                prompt = prompt_template.format(
                    cv_text=cv_text[:6000],
                    job_text=job_text[:2000],
                )
                result = call_gemini(api_key, prompt)
                st.session_state["last_analysis_time"] = time.time()
                st.session_state["last_result"] = result
                st.session_state["last_t"] = t
            except Exception as e:
                err = str(e).lower()
                if "api_key" in err or "invalid" in err or "401" in err:
                    st.error(t["error_api"])
                else:
                    st.error(t["error_generic"])
                    st.exception(e)
                st.stop()

    # ── Resultado ──────────────────────────────────────────────────
    result = st.session_state.get("last_result")
    t_res  = st.session_state.get("last_t", t)

    if result:
        st.divider()
        render_score(result.get("score", 0), t_res["score_label"])
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"#### {t_res['section_strengths']}")
            render_list(result.get("strengths", []))
            st.markdown(f"#### {t_res['section_keywords']}")
            keywords = result.get("missing_keywords", [])
            st.markdown(" ".join([f"`{kw}`" for kw in keywords]))

        with col2:
            st.markdown(f"#### {t_res['section_gaps']}")
            render_list(result.get("gaps", []))
            st.markdown(f"#### {t_res['section_suggestions']}")
            render_list(result.get("suggestions", []))

        st.divider()
        st.markdown(f"#### {t_res['section_summary']}")
        st.info(result.get("summary", ""))

    # ── Footer ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f"<p style='text-align:center;color:#aaa;font-size:12px'>{t['footer']}</p>",
        unsafe_allow_html=True,
    )

if __name__ == "__main__":
    main()