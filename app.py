import os
import re
import html as html_lib
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Pulse Radar",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# DESIGN TOKENS & CUSTOM CSS
# =============================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary: #0A0D14;
    --bg-surface: #12161F;
    --bg-surface-hover: #171C27;
    --border-subtle: rgba(255,255,255,0.07);
    --border-strong: rgba(255,255,255,0.16);
    --text-primary: #E7E9EE;
    --text-secondary: #8A93A6;
    --text-tertiary: #565F72;
    --accent-emerald: #22C55E;
    --accent-emerald-soft: rgba(34,197,94,0.12);
    --accent-rose: #F1495D;
    --accent-rose-soft: rgba(241,73,93,0.12);
    --accent-violet: #8B7CF6;
    --accent-violet-soft: rgba(139,124,246,0.14);
    --accent-blue: #4C8DF6;
}

html, body, [class*="css"], .stApp {
    background-color: var(--bg-primary) !important;
    font-family: 'Inter', -apple-system, sans-serif;
    color: var(--text-primary);
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}

.block-container {
    padding-top: 1.6rem;
    padding-bottom: 6rem;
    max-width: 880px;
    margin-left: auto;
    margin-right: auto;
}

/* ---------- HEADER ---------- */
.pr-header {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin-bottom: 26px;
}
.pr-logo {
    width: 46px;
    height: 46px;
    border-radius: 13px;
    background: linear-gradient(135deg, var(--accent-violet-soft), var(--accent-emerald-soft));
    border: 1px solid var(--border-subtle);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
}
.pr-title-row {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}
.pr-title {
    font-family: 'Sora', sans-serif;
    font-size: 28px;
    font-weight: 700;
    margin: 0;
    color: var(--text-primary);
    letter-spacing: -0.01em;
}
.pr-live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 11px;
    border-radius: 999px;
    background: var(--accent-emerald-soft);
    border: 1px solid rgba(34,197,94,0.28);
    color: var(--accent-emerald);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.03em;
}
.pr-live-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent-emerald);
    animation: pr-pulse 1.8s ease-in-out infinite;
}
@keyframes pr-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.55); opacity: 1; }
    50% { box-shadow: 0 0 0 5px rgba(34,197,94,0); opacity: 0.65; }
}
.pr-subtitle {
    margin: 6px 0 0 0;
    font-size: 14.5px;
    color: var(--text-secondary);
    line-height: 1.5;
}

/* ---------- QUICK FILTER BUTTONS ---------- */
div[data-testid="stButton"] > button {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 999px;
    color: var(--text-primary);
    font-weight: 500;
    font-size: 13.5px;
    padding: 10px 14px;
    transition: border-color 0.15s ease, transform 0.15s ease, background 0.15s ease;
}
div[data-testid="stButton"] > button:hover {
    border-color: var(--border-strong);
    background: var(--bg-surface-hover);
    transform: translateY(-1px);
    color: var(--text-primary);
}
div[data-testid="stButton"] > button:active {
    transform: translateY(0px);
}

/* ---------- EMPTY STATE ---------- */
.pr-empty-state {
    text-align: center;
    padding: 52px 20px;
    border: 1px dashed var(--border-subtle);
    border-radius: 18px;
    margin-top: 8px;
}
.pr-empty-icon { font-size: 30px; margin-bottom: 10px; }
.pr-empty-title {
    font-family: 'Sora', sans-serif;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 4px 0;
}
.pr-empty-sub {
    font-size: 13.5px;
    color: var(--text-tertiary);
    margin: 0;
    line-height: 1.5;
}

/* ---------- USER MESSAGE ---------- */
.pr-user-msg {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-left: 2px solid var(--accent-blue);
    border-radius: 12px;
    padding: 12px 16px;
    margin: 18px 0 10px 0;
    font-size: 14.5px;
    color: var(--text-primary);
    line-height: 1.5;
}
.pr-user-label {
    display: block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    color: var(--text-tertiary);
    margin-bottom: 4px;
}

/* ---------- RESPONSE CARD ---------- */
.pr-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.028), rgba(255,255,255,0.008));
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 20px 22px 18px 22px;
    margin-bottom: 22px;
    backdrop-filter: blur(8px);
}
.pr-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 14px;
}
.pr-card-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'Sora', sans-serif;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--accent-violet);
}
.pr-card-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--text-tertiary);
}
.pr-section-label {
    font-size: 11.5px;
    font-weight: 600;
    color: var(--text-tertiary);
    margin: 0 0 4px 0;
}
.pr-bullet-list {
    list-style: none;
    padding: 0;
    margin: 4px 0 0 0;
}
.pr-bullet-list li {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 7px 0;
    font-size: 14.5px;
    line-height: 1.55;
    color: var(--text-primary);
    border-bottom: 1px solid rgba(255,255,255,0.045);
}
.pr-bullet-list li:last-child { border-bottom: none; }
.pr-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-top: 6.5px;
    flex-shrink: 0;
    background: var(--text-tertiary);
}
.pr-dot.pr-pos { background: var(--accent-emerald); box-shadow: 0 0 0 3px var(--accent-emerald-soft); }
.pr-dot.pr-neg { background: var(--accent-rose); box-shadow: 0 0 0 3px var(--accent-rose-soft); }
.pr-analysis-box {
    background: rgba(139,124,246,0.06);
    border: 1px solid var(--accent-violet-soft);
    border-radius: 12px;
    padding: 13px 15px;
    margin-top: 16px;
}
.pr-analysis-title { color: var(--accent-violet); margin-bottom: 6px; }
.pr-analysis-box p {
    font-size: 14px;
    line-height: 1.6;
    color: var(--text-primary);
    margin: 0 0 8px 0;
}
.pr-analysis-box p:last-child { margin-bottom: 0; }
.pr-sources-title { margin-top: 16px; }
.pr-sources-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 6px;
}
.pr-source-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 999px;
    padding: 5px 11px;
    font-size: 12px;
    color: var(--text-secondary) !important;
    text-decoration: none !important;
    transition: border-color 0.15s ease, color 0.15s ease;
}
.pr-source-badge:hover {
    border-color: var(--accent-blue);
    color: var(--text-primary) !important;
}
.pr-no-source {
    font-size: 12.5px;
    color: var(--text-tertiary);
    font-style: italic;
}

/* ---------- CHAT INPUT (best-effort theming; Streamlit internals can shift between versions) ---------- */
[data-testid="stChatInput"] textarea {
    background: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 14px !important;
}
[data-testid="stBottom"] {
    background: var(--bg-primary) !important;
}

/* ---------- MOBILE RESPONSIVE ---------- */
@media (max-width: 640px) {
    .pr-title { font-size: 22px; }
    .pr-logo { width: 40px; height: 40px; font-size: 18px; }
    .pr-card { padding: 16px 16px 14px 16px; }
    .block-container { padding-left: 0.9rem; padding-right: 0.9rem; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================
GEMINI_MODEL = "gemini-3.6-flash"

QUICK_FILTERS = {
    "🔥 Top Trending Indo": (
        "Kamu adalah analis intelijen berita. Cari dan rangkum topik-topik yang "
        "SEDANG PALING RAMAI diperbincangkan di Indonesia hari ini, mencakup isu "
        "sosial, politik, hiburan, dan viral di media sosial. Sertakan angka atau "
        "data konkret (misalnya jumlah kasus, statistik, atau skala kejadian) bila tersedia."
    ),
    "📈 Market & Crypto Pulse": (
        "Kamu adalah analis pasar. Berikan ringkasan pergerakan pasar HARI INI, "
        "mencakup secara spesifik: level dan persentase perubahan IHSG, nilai tukar "
        "Rupiah terhadap Dolar AS (USD/IDR), level indeks S&P 500, dan harga Bitcoin "
        "(BTC) dalam USD. Sebutkan angka konkret untuk setiap instrumen beserta faktor "
        "pemicu utamanya."
    ),
    "⚽ Dunia Olahraga": (
        "Kamu adalah jurnalis olahraga. Rangkum berita dan hasil pertandingan paling "
        "penting dan terbaru dari dunia olahraga hari ini, terutama sepak bola "
        "(liga-liga besar dan Timnas Indonesia jika ada), serta cabang olahraga populer "
        "lain. Sertakan skor atau hasil konkret bila tersedia."
    ),
    "🤖 Tech & AI Innovations": (
        "Kamu adalah analis teknologi. Rangkum inovasi, peluncuran produk, atau berita "
        "paling signifikan seputar teknologi dan kecerdasan buatan (AI) dalam beberapa "
        "hari terakhir. Sertakan nama perusahaan/produk dan detail teknis konkret bila "
        "relevan."
    ),
}

SYSTEM_INSTRUCTION = (
    "Kamu adalah mesin analisis bernama Pulse Radar. Tugasmu adalah mencari informasi "
    "TERKINI melalui Google Search dan menyusunnya menjadi jawaban yang padat, akurat, "
    "dan berbasis data. Gunakan HANYA fakta yang bisa kamu temukan lewat pencarian, "
    "jangan mengarang.\n\n"
    "Format jawabanmu HARUS PERSIS mengikuti struktur berikut, gunakan penanda ini apa "
    "adanya tanpa tambahan simbol markdown lain seperti '**' atau '#':\n\n"
    "###RINGKASAN###\n"
    "(3-5 poin ringkasan eksekutif, satu poin per baris diawali tanda '- ', to the "
    "point, sertakan angka/data konkret jika ada)\n\n"
    "###ANALISIS###\n"
    "(1-2 paragraf singkat berisi analisis dampak, konteks, atau alasan di balik "
    "peristiwa tersebut, bahasa lugas dan tidak berlebihan)\n\n"
    "Jangan menuliskan daftar sumber atau URL secara manual di dalam teks, karena "
    "sumber akan diambil otomatis dari data pencarian. Jangan menambahkan bagian atau "
    "penanda lain di luar dua penanda tersebut."
)

POSITIVE_KEYWORDS = [
    "naik", "menguat", "melonjak", "rally", "surplus", "profit", "positif",
    "meningkat", "tumbuh", "cetak rekor", "all-time high", "reli",
]
NEGATIVE_KEYWORDS = [
    "turun", "melemah", "anjlok", "drop", "defisit", "rugi", "negatif",
    "menurun", "terkoreksi", "tergerus", "merosot",
]

# =============================================================================
# HELPER: API KEY DETECTION (mendukung local env var & Streamlit Cloud Secrets)
# =============================================================================
def get_env_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if key:
        return key
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


# =============================================================================
# SESSION STATE
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = get_env_api_key()
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def sentiment_class(line: str) -> str:
    lower = line.lower()
    if any(k in lower for k in NEGATIVE_KEYWORDS):
        return "pr-neg"
    if any(k in lower for k in POSITIVE_KEYWORDS):
        return "pr-pos"
    return ""


def bullets_to_html(text: str) -> str:
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return (
            "<p style='color:var(--text-secondary); font-size:14px;'>"
            "Tidak ada ringkasan yang bisa ditampilkan.</p>"
        )
    items = []
    for line in lines:
        clean = re.sub(r"^[-•*]\s*", "", line).strip()
        if not clean:
            continue
        cls = sentiment_class(clean)
        dot_class = f"pr-dot {cls}".strip()
        items.append(
            f"<li><span class='{dot_class}'></span><span>{html_lib.escape(clean)}</span></li>"
        )
    return f"<ul class='pr-bullet-list'>{''.join(items)}</ul>"


def paragraphs_to_html(text: str) -> str:
    text = text.strip()
    if not text:
        return (
            "<p style='color:var(--text-secondary); font-size:14px;'>"
            "Tidak ada analisis tambahan.</p>"
        )
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [text]
    return "".join(f"<p>{html_lib.escape(p)}</p>" for p in paras)


def sources_to_html(sources: list) -> str:
    if not sources:
        return (
            "<span class='pr-no-source'>Tidak ada sumber eksternal spesifik yang "
            "terdeteksi untuk jawaban ini.</span>"
        )
    badges = []
    for s in sources[:8]:
        raw_title = s.get("title") or s.get("url") or "Sumber"
        title = raw_title if len(raw_title) <= 42 else raw_title[:42] + "…"
        title = html_lib.escape(title)
        url = html_lib.escape(s.get("url", "#"))
        badges.append(
            f"<a href='{url}' target='_blank' rel='noopener' class='pr-source-badge'>"
            f"🔗 {title}</a>"
        )
    return "".join(badges)


def parse_gemini_response(response) -> tuple:
    text = getattr(response, "text", None) or ""

    summary_match = re.search(r"###RINGKASAN###(.*?)###ANALISIS###", text, re.DOTALL)
    analysis_match = re.search(r"###ANALISIS###(.*)", text, re.DOTALL)

    if summary_match:
        summary_raw = summary_match.group(1).strip()
    else:
        summary_raw = text.strip()

    analysis_raw = analysis_match.group(1).strip() if analysis_match else ""

    sources = []
    try:
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            grounding_metadata = getattr(candidates[0], "grounding_metadata", None)
            chunks = (
                getattr(grounding_metadata, "grounding_chunks", None)
                if grounding_metadata
                else None
            )
            if chunks:
                seen_urls = set()
                for chunk in chunks:
                    web = getattr(chunk, "web", None)
                    if web is not None and getattr(web, "uri", None):
                        uri = web.uri
                        if uri not in seen_urls:
                            seen_urls.add(uri)
                            sources.append(
                                {"title": getattr(web, "title", None) or uri, "url": uri}
                            )
    except Exception:
        sources = []

    return summary_raw, analysis_raw, sources


def call_pulse_radar(prompt: str, api_key: str):
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.4,
    )
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config,
    )
    return response


def process_prompt(raw_prompt: str, display_label: str = None):
    display_text = display_label if display_label else raw_prompt
    st.session_state.messages.append({"role": "user", "content": display_text})

    api_key = st.session_state.api_key
    timestamp = datetime.now().strftime("%H:%M")

    if not api_key:
        st.session_state.messages.append({
            "role": "assistant",
            "summary_html": (
                "<p style='color:var(--accent-rose); font-size:14px;'>⚠️ Gemini API "
                "Key belum diisi. Masukkan API key kamu di sidebar terlebih dahulu.</p>"
            ),
            "analysis_html": "",
            "sources_html": "",
            "timestamp": timestamp,
        })
        return

    try:
        response = call_pulse_radar(raw_prompt, api_key)
        summary_raw, analysis_raw, sources = parse_gemini_response(response)
        st.session_state.messages.append({
            "role": "assistant",
            "summary_html": bullets_to_html(summary_raw),
            "analysis_html": paragraphs_to_html(analysis_raw),
            "sources_html": sources_to_html(sources),
            "timestamp": timestamp,
        })
    except Exception as e:
        error_text = html_lib.escape(str(e))
        st.session_state.messages.append({
            "role": "assistant",
            "summary_html": (
                f"<p style='color:var(--accent-rose); font-size:14px;'>⚠️ Terjadi "
                f"kesalahan saat mengambil data: {error_text}</p>"
            ),
            "analysis_html": (
                "<p style='font-size:13.5px; color:var(--text-secondary);'>Periksa "
                "kembali API Key kamu di sidebar, atau coba lagi dalam beberapa "
                "saat.</p>"
            ),
            "sources_html": "",
            "timestamp": timestamp,
        })


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("### ⚙️ Konfigurasi")

    env_key = get_env_api_key()
    if env_key:
        st.success("API Key terdeteksi dari environment variable.")
        st.session_state.api_key = env_key
    else:
        key_input = st.text_input(
            "Gemini API Key",
            type="password",
            value=st.session_state.api_key,
            placeholder="Tempel API key kamu di sini",
            help="Dapatkan API key gratis di Google AI Studio (aistudio.google.com).",
        )
        st.session_state.api_key = key_input
        if st.session_state.api_key:
            st.success("API Key tersimpan untuk sesi ini.")
        else:
            st.warning("Belum ada API Key aktif.")

    st.divider()
    st.caption(
        "Pulse Radar menggunakan model **Gemini 3.6 Flash** dengan **Google Search "
        "Grounding** sehingga jawaban selalu berbasis pencarian data terkini di web."
    )
    st.divider()

    if st.button("🗑️ Hapus Riwayat Percakapan", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# =============================================================================
# HEADER
# =============================================================================
st.markdown(
    """
    <div class="pr-header">
        <div class="pr-logo">📡</div>
        <div>
            <div class="pr-title-row">
                <h1 class="pr-title">Pulse Radar</h1>
                <span class="pr-live-badge"><span class="pr-live-dot"></span>LIVE RADAR</span>
            </div>
            <p class="pr-subtitle">
                Dashboard intelijen berita, tren, dan pasar real-time — memindai web
                lewat Gemini AI untuk kamu.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# QUICK FILTER PILLS
# =============================================================================
filter_items = list(QUICK_FILTERS.items())
row1 = st.columns(2)
row2 = st.columns(2)
filter_columns = row1 + row2

for col, (label, base_prompt) in zip(filter_columns, filter_items):
    with col:
        if st.button(label, use_container_width=True, key=f"filter_{label}"):
            st.session_state.pending_prompt = (base_prompt, label)

st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

# =============================================================================
# CONVERSATION HISTORY
# =============================================================================
if not st.session_state.messages:
    st.markdown(
        """
        <div class="pr-empty-state">
            <div class="pr-empty-icon">🛰️</div>
            <p class="pr-empty-title">Pulse Radar siap memindai.</p>
            <p class="pr-empty-sub">
                Pilih salah satu radar cepat di atas, atau ketik pertanyaanmu sendiri
                di kolom chat di bagian bawah layar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="pr-user-msg">
                    <span class="pr-user-label">kamu tanya</span>
                    {html_lib.escape(msg['content'])}
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="pr-card">
                    <div class="pr-card-header">
                        <span class="pr-card-badge">📡 Pulse Radar</span>
                        <span class="pr-card-time">{msg['timestamp']}</span>
                    </div>
                    <p class="pr-section-label">Ringkasan Eksekutif</p>
                    {msg['summary_html']}
                    <div class="pr-analysis-box">
                        <p class="pr-section-label pr-analysis-title">📊 Analisis &amp; Dampak</p>
                        {msg['analysis_html']}
                    </div>
                    <p class="pr-section-label pr-sources-title">Sumber</p>
                    <div class="pr-sources-row">{msg['sources_html']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# =============================================================================
# HANDLE QUICK FILTER CLICK
# =============================================================================
if st.session_state.pending_prompt is not None:
    base_prompt, label = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
    with st.spinner("Pulse Radar sedang memindai sumber terkini..."):
        process_prompt(base_prompt, display_label=label)
    st.rerun()

# =============================================================================
# FREE CHAT INPUT
# =============================================================================
user_query = st.chat_input("Tanya apa saja... misal: 'market hari ini kenapa drop bro?'")
if user_query:
    with st.spinner("Pulse Radar sedang memindai sumber terkini..."):
        process_prompt(user_query)
    st.rerun()
