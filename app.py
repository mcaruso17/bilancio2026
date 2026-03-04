import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from auth import Authenticator
from permissions import puo_modificare, is_admin
from database import init_database, get_connection
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from load_users import genera_email, genera_password

start_time = datetime.now()
start_time_str = start_time.strftime("%d/%m/%Y %H:%M:%S")

# ======================================================================
#                    IMPOSTAZIONI DA MODIFICARE
# ======================================================================

BILANCIO_CSV = "bilancio2026.csv"
MAPPATURA_FILE = "mappatura_uffici.json"

UFFICI = [
    "I", "II", "III", "IV", "V", "VI", "VII",
    "VIII", "IX", "X", "XI", "XII", "XIII",
]

# ======================================================================
#          FINE IMPOSTAZIONI - DA QUI IN GIU NON TOCCARE
# ======================================================================

# Inizializza database e autenticatore
init_database()
auth = Authenticator()

st.set_page_config(
    page_title="Navigatore LdB 2026 -- Ragioneria Generale dello Stato",
    layout="wide",
    initial_sidebar_state="expanded",
)

MEF_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;600;700&display=swap');

/* -- Design tokens -- */
:root {
    --mef-blue:       #1D3D8F;
    --mef-blue-dark:  #132B6B;
    --mef-blue-light: #E8EDF7;
    --mef-gold:       #C49B1D;
    --mef-border:     #CED5E8;
    --font: 'Segoe UI', 'Source Sans 3', sans-serif;
}

/* ---- DARK-MODE NEUTRALISATION ---- */
[data-theme="dark"] .main,
[data-theme="dark"] .block-container,
[data-theme="dark"] section[data-testid="stMain"],
[data-theme="dark"] section[data-testid="stMain"] > div,
[data-theme="dark"] [data-testid="stAppViewContainer"] {
    background-color: #FFFFFF !important;
    color: #17203A !important;
}
[data-theme="dark"] p,
[data-theme="dark"] span:not([class*="mef-"]):not([class*="sb-"]):not([class*="doc-"]):not([class*="tag-"]),
[data-theme="dark"] div:not([class*="mef-"]):not([class*="sb-"]):not([class*="card-"]),
[data-theme="dark"] li { color: #17203A !important; }
[data-theme="dark"] .streamlit-expanderHeader,
[data-theme="dark"] details summary {
    background-color: #FFFFFF !important;
    color: #17203A !important;
    border-color: #CED5E8 !important;
}
[data-theme="dark"] .streamlit-expanderContent,
[data-theme="dark"] details > div {
    background-color: #FFFFFF !important;
    color: #17203A !important;
    border-color: #CED5E8 !important;
}
[data-theme="dark"] input,
[data-theme="dark"] .stTextInput input {
    background-color: #FFFFFF !important;
    color: #17203A !important;
    border-color: #CED5E8 !important;
}
[data-theme="dark"] .stTextInput label,
[data-theme="dark"] .stSelectbox label,
[data-theme="dark"] .stMultiSelect label,
[data-theme="dark"] label { color: #556080 !important; }
[data-theme="dark"] [data-baseweb="tab-list"],
[data-theme="dark"] [data-baseweb="tab"],
[data-theme="dark"] [data-baseweb="tab-panel"] {
    background-color: #FFFFFF !important;
    color: #17203A !important;
}
[data-theme="dark"] [aria-selected="true"] {
    color: #1D3D8F !important;
    border-bottom-color: #1D3D8F !important;
}
[data-theme="dark"] table,
[data-theme="dark"] tbody,
[data-theme="dark"] tr,
[data-theme="dark"] td {
    background-color: #FFFFFF !important;
    color: #17203A !important;
    border-color: #CED5E8 !important;
}
[data-theme="dark"] th {
    background-color: #1D3D8F !important;
    color: #FFFFFF !important;
}
[data-theme="dark"] tr:nth-child(even) td {
    background-color: #F5F6F8 !important;
}
[data-theme="dark"] .stAlert,
[data-theme="dark"] .stAlert > div {
    background-color: #E8EDF7 !important;
    color: #17203A !important;
}
[data-theme="dark"] [data-baseweb="select"] div,
[data-theme="dark"] [data-baseweb="popover"] * {
    background-color: #FFFFFF !important;
    color: #17203A !important;
}
/* Keep sidebar dark */
[data-theme="dark"] [data-testid="stSidebar"],
[data-theme="dark"] [data-testid="stSidebar"] * {
    background-color: #132B6B !important;
    color: rgba(255,255,255,0.82) !important;
}
[data-theme="dark"] [data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #FFFFFF !important;
}

/* ---- BASE ---- */
html, body, [class*="css"] { font-family: var(--font) !important; }
.main,
section[data-testid="stMain"],
[data-testid="stAppViewContainer"] {
    background-color: #FFFFFF !important;
    color: #17203A !important;
}
.block-container {
    padding-top: 0 !important;
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
    background-color: #FFFFFF !important;
}

/* ---- INSTITUTIONAL HEADER ---- */
.mef-header {
    background: #1D3D8F;
    border-bottom: 4px solid #C49B1D;
    margin: -1rem -1rem 0 -1rem;
}
.mef-header-inner {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 14px 40px;
}
.mef-header-ministry {
    font-size: 11px; font-weight: 300;
    color: rgba(255,255,255,0.62); letter-spacing: .04em;
}
.mef-header-dept {
    font-size: 16px; font-weight: 700;
    color: #FFFFFF; line-height: 1.2;
}
.mef-header-sub {
    font-size: 10px; font-weight: 300;
    color: rgba(255,255,255,0.48);
    letter-spacing: .07em; text-transform: uppercase; margin-top: 3px;
}
.mef-header-right { margin-left: auto; text-align: right; }
.mef-app-name {
    font-size: 22px; font-weight: 700;
    color: #FFFFFF; letter-spacing: .03em; line-height: 1;
}
.mef-app-tagline {
    font-size: 10px; color: rgba(255,255,255,0.48);
    font-weight: 300; letter-spacing: .08em;
    text-transform: uppercase; margin-top: 3px;
}

/* ---- PAGE TITLE / DIVIDER ---- */
.mef-rule { border: none; border-top: 1px solid #CED5E8; margin: 1.25rem 0; }
.mef-page-title {
    font-size: 21px; font-weight: 700; color: #1D3D8F;
    margin: 1.5rem 0 .2rem 0; letter-spacing: -.01em;
    font-family: var(--font);
}
.mef-page-subtitle {
    font-size: 13px; color: #556080;
    margin-bottom: 1.25rem; line-height: 1.5;
    font-family: var(--font);
}

/* ---- TAGS ---- */
.mef-tag {
    display: inline-block; padding: 2px 7px; border-radius: 2px;
    font-size: 10px; font-weight: 700; letter-spacing: .07em;
    text-transform: uppercase; font-family: var(--font); line-height: 1.6;
}
.tag-nav { background-color: #1D3D8F; color: #FFFFFF; }
.tag-map { background-color: #C49B1D; color: #FFFFFF; }

/* ---- STATUS CARDS ---- */
.mef-status-row { display: flex; gap: 10px; margin-bottom: 1.5rem; flex-wrap: wrap; }
.mef-status-card {
    flex: 1; min-width: 200px; border-radius: 3px;
    padding: 9px 14px; font-size: 13px; font-family: var(--font);
    display: flex; align-items: center; gap: 10px; border: 1px solid;
    background-color: #EDF2FF; border-color: #1D3D8F; color: #132B6B;
}
.mef-status-card.error {
    background-color: #FFF3F3; border-color: #CC2222; color: #8B0000;
}
.mef-status-dot {
    width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
    background: #1D3D8F;
}
.mef-status-card.error .mef-status-dot { background: #CC2222; }
.mef-status-tag {
    font-size: 9px; font-weight: 700; letter-spacing: .08em;
    text-transform: uppercase; padding: 2px 6px; border-radius: 2px;
    margin-left: auto; flex-shrink: 0;
    background: #1D3D8F; color: #FFFFFF;
}

/* ---- SEARCH INPUT ---- */
.stTextInput > div > div > input {
    border: 1.5px solid #CED5E8 !important;
    border-radius: 3px !important; font-size: 14px !important;
    padding: 10px 14px !important; font-family: var(--font) !important;
    background-color: #FFFFFF !important; color: #17203A !important;
    transition: border-color .2s;
}
.stTextInput > div > div > input:focus {
    border-color: #1D3D8F !important;
    box-shadow: 0 0 0 3px rgba(29,61,143,.10) !important;
}
.stTextInput > label {
    font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: .07em !important;
    color: #556080 !important; font-family: var(--font) !important;
}

/* ---- MULTISELECT ---- */
.stMultiSelect > label {
    font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: .07em !important;
    color: #556080 !important; font-family: var(--font) !important;
}
.stMultiSelect [data-baseweb="select"] {
    background-color: #FFFFFF !important;
}
.stMultiSelect [data-baseweb="tag"] {
    background-color: #1D3D8F !important;
    color: #FFFFFF !important;
    border-radius: 2px !important;
    font-size: 12px !important;
}

/* ---- SELECTBOX ---- */
.stSelectbox > label {
    font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: .07em !important;
    color: #556080 !important; font-family: var(--font) !important;
}
.stSelectbox [data-baseweb="select"] div {
    background-color: #FFFFFF !important; color: #17203A !important;
}

/* ---- TABS ---- */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid #CED5E8 !important;
    gap: 0 !important; background-color: #FFFFFF !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--font) !important; font-size: 13px !important;
    font-weight: 600 !important; color: #556080 !important;
    padding: 10px 20px !important; border-radius: 0 !important;
    border-bottom: 3px solid transparent !important;
    margin-bottom: -2px !important; background-color: #FFFFFF !important;
}
.stTabs [aria-selected="true"] {
    color: #1D3D8F !important;
    border-bottom-color: #1D3D8F !important;
    background-color: #FFFFFF !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.25rem !important; background-color: #FFFFFF !important;
}

/* ---- EXPANDER / DOCUMENT CARDS ---- */
.streamlit-expanderHeader, details summary {
    background-color: #FFFFFF !important;
    border: 1px solid #CED5E8 !important; border-radius: 3px !important;
    font-family: var(--font) !important; font-size: 13.5px !important;
    font-weight: 600 !important; color: #132B6B !important;
    padding: 11px 16px !important;
}
.streamlit-expanderHeader:hover, details summary:hover {
    background-color: #E8EDF7 !important;
}
.streamlit-expanderContent, details > div {
    border: 1px solid #CED5E8 !important; border-top: none !important;
    border-radius: 0 0 3px 3px !important; padding: 16px 20px !important;
    background-color: #FFFFFF !important; color: #17203A !important;
}

/* ---- TABLE ---- */
table {
    font-size: 12.5px !important; border-collapse: collapse !important;
    width: 100% !important; font-family: var(--font) !important;
    background-color: #FFFFFF !important;
}
th {
    background-color: #1D3D8F !important; color: #FFFFFF !important;
    font-size: 10.5px !important; font-weight: 700 !important;
    letter-spacing: .07em !important; text-transform: uppercase !important;
    padding: 8px 12px !important; border: none !important;
}
td {
    padding: 7px 12px !important; border-bottom: 1px solid #CED5E8 !important;
    vertical-align: top !important; color: #17203A !important;
    background-color: #FFFFFF !important;
}
tr:nth-child(even) td { background-color: #F5F6F8 !important; }

/* ---- METRICS ---- */
[data-testid="stMetricValue"] {
    color: #1D3D8F !important;
    font-weight: 700 !important;
    font-family: var(--font) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: .05em !important;
    color: #556080 !important;
    font-family: var(--font) !important;
}

/* ---- BUTTONS ---- */
.stButton > button[kind="primary"],
.stDownloadButton > button {
    background-color: #1D3D8F !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 3px !important;
    font-family: var(--font) !important;
    font-weight: 600 !important;
    letter-spacing: .03em !important;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button:hover {
    background-color: #132B6B !important;
}

/* ---- SIDEBAR ---- */
[data-testid="stSidebar"] {
    background-color: #132B6B !important;
    border-right: 3px solid #C49B1D !important;
}
[data-testid="stSidebar"] * {
    font-family: var(--font) !important;
    color: rgba(255,255,255,.82) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #FFFFFF !important; font-size: 11px !important;
    font-weight: 700 !important; text-transform: uppercase !important;
    letter-spacing: .08em !important;
    border-bottom: 1px solid rgba(255,255,255,.15) !important;
    padding-bottom: 5px !important; margin-top: 14px !important;
}
[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    font-size: 20px !important; font-weight: 700 !important;
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
    font-size: 9.5px !important; text-transform: uppercase !important;
    letter-spacing: .07em !important; color: rgba(255,255,255,.50) !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12) !important; }
/* Sidebar radio buttons */
[data-testid="stSidebar"] .stRadio label {
    color: rgba(255,255,255,.82) !important;
    font-size: 13px !important;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] div {
    background-color: transparent !important;
}

/* ---- SIDEBAR ALWAYS VISIBLE ---- */
[data-testid="stSidebar"] {
    margin-left: 0 !important;
    transform: none !important;
    width: 300px !important;
    min-width: 300px !important;
}
[data-testid="stSidebar"][aria-expanded="false"] {
    margin-left: 0 !important;
    transform: none !important;
    width: 300px !important;
    min-width: 300px !important;
}
/* Hide collapse/expand buttons */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

/* ---- FIX: STREAMLIT NATIVE HEADER BAR (white stripe) ---- */
header[data-testid="stHeader"] {
    background-color: transparent !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    pointer-events: none !important;
}
header[data-testid="stHeader"] * {
    pointer-events: auto !important;
}
header[data-testid="stHeader"] [data-testid="stToolbar"] {
    display: none !important;
}

/* ---- HIDE STREAMLIT CHROME ---- */
#MainMenu                              { display: none !important; }
footer                                 { display: none !important; }
[data-testid="stToolbar"]             { display: none !important; }
[data-testid="stDecoration"]          { display: none !important; }
[data-testid="stStatusWidget"]        { display: none !important; }

/* ---- FOOTER ---- */
.mef-footer {
    border-top: 1px solid #CED5E8; margin-top: 3rem; padding-top: 1rem;
    font-size: 11px; color: #556080; font-family: var(--font);
    display: flex; justify-content: space-between;
    flex-wrap: wrap; gap: 4px; background-color: #FFFFFF;
}
</style>
"""

st.markdown(MEF_CSS, unsafe_allow_html=True)


# ===================================================================
#  AUTENTICAZIONE
# ===================================================================

def pagina_login():
    """Mostra il form di login"""
    st.markdown("""
    <div class="mef-header">
      <div class="mef-header-inner">
        <div>
          <div class="mef-header-ministry">Ministero dell'Economia e delle Finanze</div>
          <div class="mef-header-dept">Ragioneria Generale dello Stato</div>
          <div class="mef-header-sub">Navigatore Legge di Bilancio</div>
        </div>
        <div class="mef-header-right">
          <div class="mef-app-name">LdB 2026</div>
          <div class="mef-app-tagline">Navigatore e Mappatura Uffici</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="mef-page-title">Accesso Area Riservata</div>', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-subtitle">Inserisci le credenziali fornite dall\'amministratore</div>', unsafe_allow_html=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Accedi"):
        successo, messaggio = auth.login(email, password)
        if successo:
            st.rerun()
        else:
            st.error(messaggio)

def pagina_cambio_password():
    """Forza il cambio password al primo accesso"""
    st.markdown("""
    <div class="mef-header">
      <div class="mef-header-inner">
        <div>
          <div class="mef-header-ministry">Ministero dell'Economia e delle Finanze</div>
          <div class="mef-header-dept">Ragioneria Generale dello Stato</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="mef-page-title">Cambio Password Obbligatorio</div>', unsafe_allow_html=True)
    st.warning("Devi cambiare la password prima di continuare")

    attuale = st.text_input("Password attuale", type="password")
    nuova = st.text_input("Nuova password", type="password")
    conferma = st.text_input("Conferma password", type="password")

    if st.button("Cambia password"):
        if nuova != conferma:
            st.error("Le password non coincidono")
        else:
            successo, messaggio = auth.cambia_password(attuale, nuova)
            if successo:
                st.success(messaggio)
                st.rerun()
            else:
                st.error(messaggio)

def pagina_carica_utenti():
    """Permette all'admin di caricare utenti da Excel"""
    st.markdown('<div class="mef-page-title">Caricamento Utenti</div>', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-subtitle">Area riservata all\'amministratore del sistema</div>', unsafe_allow_html=True)

    if "admin_autenticato" not in st.session_state:
        st.session_state.admin_autenticato = False
    if "credenziali_generate" not in st.session_state:
        st.session_state.credenziali_generate = None

    if not st.session_state.admin_autenticato:
        username = st.text_input("Username admin")
        password = st.text_input("Password admin", type="password")
        if st.button("Accedi come admin"):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_autenticato = True
                st.rerun()
            else:
                st.error("Credenziali admin non valide")
        return

    st.success("Accesso admin confermato")

    if st.session_state.credenziali_generate is not None:
        st.subheader("Credenziali generate")
        df_cred = pd.DataFrame(st.session_state.credenziali_generate)
        st.dataframe(df_cred)
        st.download_button(
            "Scarica credenziali CSV",
            df_cred.to_csv(index=False),
            "credenziali_temporanee.csv",
            "text/csv",
        )
        st.warning("Scarica il file, distribuisci le password e poi eliminalo!")
        if st.button("Pulisci credenziali dalla schermata"):
            st.session_state.credenziali_generate = None
            st.rerun()
        return

    file = st.file_uploader("Carica il file Excel del personale", type=["xlsx"])

    if file and st.button("Carica utenti"):
        df_users = pd.read_excel(file)
        df_users.columns = df_users.columns.str.strip().str.lower()
        df_users = df_users.dropna(subset=["nominativo"])
        credenziali = []

        for _, riga in df_users.iterrows():
            nominativo = riga["nominativo"]
            email = genera_email(nominativo)
            password_utente = genera_password()

            pw_hash, salt = Authenticator.hash_password(password_utente)
            stored = f"{pw_hash}:{salt}"

            with get_connection() as conn:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO users
                        (nominativo, email, password_hash, ruolo, ufficio, stanza, interno, cellulare)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            nominativo, email, stored,
                            riga["ruolo"], str(riga["ufficio"]),
                            str(riga.get("stanza", "")),
                            str(riga.get("interno", "")),
                            str(riga.get("cellulare", ""))
                        )
                    )
                    credenziali.append({
                        "nominativo": nominativo,
                        "email": email,
                        "password": password_utente
                    })
                except Exception as e:
                    st.error(f"Errore per {nominativo}: {e}")

        if credenziali:
            st.session_state.credenziali_generate = credenziali
            st.success(f"Caricati {len(credenziali)} utenti!")
            st.rerun()

def pannello_admin():
    """Pannello per il direttore: reset password"""
    with st.expander("Gestione Utenti - Reset Password"):
        with get_connection() as conn:
            utenti = conn.execute(
                "SELECT id, nominativo, email FROM users WHERE attivo = 1"
            ).fetchall()

        utente_scelto = st.selectbox(
            "Seleziona utente",
            utenti,
            format_func=lambda u: f"{u['nominativo']} ({u['email']})"
        )

        if st.button("Reset Password"):
            nuova_pw = Authenticator.reset_password(utente_scelto["id"])
            st.success(f"Nuova password temporanea: {nuova_pw}")
            st.warning("Comunicala all'utente e poi chiudi questa pagina")

# --- Controllo accesso ---
if not st.session_state.authenticated:
    tab_login, tab_admin = st.tabs(["Login", "Carica Utenti"])
    with tab_login:
        pagina_login()
    with tab_admin:
        pagina_carica_utenti()
    st.stop()

if st.session_state.deve_cambiare_password:
    pagina_cambio_password()
    st.stop()


# ===================================================================
#  DA QUI IN GIU: UTENTE AUTENTICATO
# ===================================================================


# ===================================================================
#  INSTITUTIONAL HEADER
# ===================================================================

st.markdown("""
<div class="mef-header">
  <div class="mef-header-inner">
    <div>
      <div class="mef-header-ministry">Ministero dell'Economia e delle Finanze</div>
      <div class="mef-header-dept">Ragioneria Generale dello Stato</div>
      <div class="mef-header-sub">Navigatore Legge di Bilancio</div>
    </div>
    <div class="mef-header-right">
      <div class="mef-app-name">LdB 2026</div>
      <div class="mef-app-tagline">Navigatore e Mappatura Uffici</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ===================================================================
#  CARICAMENTO DATI
# ===================================================================

@st.cache_data
def load_bilancio():
    if not os.path.exists(BILANCIO_CSV):
        return pd.DataFrame()
    df = pd.read_csv(BILANCIO_CSV, sep=";", encoding="utf-8-sig", low_memory=False)
    str_cols = df.select_dtypes(include="object").columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
    importo_cols = [
        "Legge di Bilancio CP A1", "Legge di Bilancio CP A2",
        "Legge di Bilancio CP A3", "Legge di Bilancio CS A1",
        "Legge di Bilancio CS A2", "Legge di Bilancio CS A3",
        "Legge di Bilancio RS A1",
    ]
    for col in importo_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


# ===================================================================
#  PERSISTENZA MAPPATURA (JSON)
# ===================================================================

def load_mappatura():
    if os.path.exists(MAPPATURA_FILE):
        try:
            with open(MAPPATURA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_mappatura(data):
    with open(MAPPATURA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===================================================================
#  HELPER
# ===================================================================

def fmt_eur(val):
    if pd.isna(val) or val == 0:
        return "EUR 0"
    return f"EUR {int(val):,.0f}".replace(",", ".")


def build_label_map(df_slice, code_col, name_col):
    pairs = (
        df_slice[[code_col, name_col]]
        .drop_duplicates()
        .sort_values(code_col)
    )
    labels = [
        f"{row[code_col]:02d} -- {row[name_col]}"
        for _, row in pairs.iterrows()
    ]
    label_to_code = {
        f"{row[code_col]:02d} -- {row[name_col]}": row[code_col]
        for _, row in pairs.iterrows()
    }
    return labels, label_to_code


# ===================================================================
#  CARICA DATI GLOBALI
# ===================================================================

df = load_bilancio()
data_ok = not df.empty

if not data_ok:
    st.markdown(f"""
    <div class="mef-status-row">
      <div class="mef-status-card error">
        <div class="mef-status-dot"></div>
        <span>File <strong>{BILANCIO_CSV}</strong> non trovato.
        Assicurati che sia nella stessa cartella dell'app.</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ===================================================================
#  STATUS INDICATOR
# ===================================================================

st.markdown(f"""
<div class="mef-page-title">Legge di Bilancio 2026</div>
<div class="mef-page-subtitle">
  Navigazione gerarchica del bilancio e mappatura uffici ispettorato
</div>
<div class="mef-status-row">
  <div class="mef-status-card">
    <div class="mef-status-dot"></div>
    <span>Dataset: <strong>{len(df):,}</strong> record --
    <strong>{df['Numero Capitolo di Spesa'].nunique():,}</strong> capitoli</span>
    <span class="mef-status-tag">LdB</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)


# ===================================================================
#  NAVIGAZIONE PAGINE
# ===================================================================

pagina = st.sidebar.radio(
    "Pagina",
    options=["Navigatore e Selezione", "Mappatura Uffici"],
    index=0,
)


# ==================================================================
#             PAGINA 1 -- NAVIGATORE E SELEZIONE
# ==================================================================

if pagina == "Navigatore e Selezione":

    # --- STEP 1 --- AMMINISTRAZIONI ---
    st.markdown('<div class="mef-page-title" style="font-size:17px">1. Amministrazioni</div>', unsafe_allow_html=True)
    amministrazioni = sorted(df["Amministrazione"].unique())
    sel_amm = st.multiselect(
        "Seleziona una o piu Amministrazioni:",
        options=amministrazioni,
        key="sel_amm",
    )
    if not sel_amm:
        st.info("Seleziona almeno un'amministrazione per iniziare.")
        st.stop()

    df_filtered = df[df["Amministrazione"].isin(sel_amm)].copy()

    # --- STEP 2 --- CENTRO RESPONSABILITA ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">2. Centro Responsabilita (Dipartimento)</div>', unsafe_allow_html=True)

    cdr_col = "Centro Responsabilita" if "Centro Responsabilita" in df_filtered.columns else "Centro Responsabilit\u00e0"
    cdr_options = sorted(df_filtered[cdr_col].unique())

    sel_cdr = st.multiselect(
        "Seleziona uno o piu Centri di Responsabilita (vuoto = tutti):",
        options=cdr_options,
        key="sel_cdr",
    )
    if sel_cdr:
        df_filtered = df_filtered[
            df_filtered[cdr_col].isin(sel_cdr)
        ].copy()

    # --- STEP 3 --- MISSIONI ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">3. Missioni</div>', unsafe_allow_html=True)

    miss_labels, miss_map = build_label_map(
        df_filtered, "Codice Missione", "Missione"
    )
    sel_miss_labels = st.multiselect(
        "Seleziona una o piu Missioni:",
        options=miss_labels,
        key="sel_miss",
    )
    if not sel_miss_labels:
        st.info("Seleziona almeno una missione.")
        st.stop()

    sel_miss_codes = [miss_map[l] for l in sel_miss_labels]
    df_filtered = df_filtered[
        df_filtered["Codice Missione"].isin(sel_miss_codes)
    ].copy()

    # --- STEP 4 --- PROGRAMMI ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">4. Programmi</div>', unsafe_allow_html=True)

    prog_labels, prog_map = build_label_map(
        df_filtered, "Codice Programma", "Programma"
    )
    sel_prog_labels = st.multiselect(
        "Seleziona uno o piu Programmi:",
        options=prog_labels,
        key="sel_prog",
    )
    if not sel_prog_labels:
        st.info("Seleziona almeno un programma.")
        st.stop()

    sel_prog_codes = [prog_map[l] for l in sel_prog_labels]
    df_filtered = df_filtered[
        df_filtered["Codice Programma"].isin(sel_prog_codes)
    ].copy()

    # --- STEP 5 --- AZIONI (opzionale) ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">5. Azioni (opzionale)</div>', unsafe_allow_html=True)

    az_labels, az_map = build_label_map(
        df_filtered, "Codice Azione", "Azione"
    )
    sel_az_labels = st.multiselect(
        "Filtra per Azioni (vuoto = tutte):",
        options=az_labels,
        key="sel_azione",
    )
    if sel_az_labels:
        sel_az_codes = [az_map[l] for l in sel_az_labels]
        df_filtered = df_filtered[
            df_filtered["Codice Azione"].isin(sel_az_codes)
        ].copy()

    # --- STEP 6 --- TITOLO (opzionale) ---
    titoli = sorted(df_filtered["Titolo"].unique())
    if len(titoli) > 1:
        sel_titoli = st.multiselect(
            "Filtra per Titolo (opzionale):",
            options=titoli,
            key="sel_titolo",
        )
        if sel_titoli:
            df_filtered = df_filtered[
                df_filtered["Titolo"].isin(sel_titoli)
            ].copy()

    # ===================================================================
    #  OUTPUT -- RISULTATI
    # ===================================================================

    df_out = df_filtered.copy()

    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">Capitoli di Spesa e Piani Gestionali</div>', unsafe_allow_html=True)

    n_cap_out = df_out["Numero Capitolo di Spesa"].nunique()
    n_pg_out = len(df_out)
    totale_cp = df_out["Legge di Bilancio CP A1"].sum()

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Capitoli di Spesa", f"{n_cap_out:,}")
    col_m2.metric("Piani Gestionali", f"{n_pg_out:,}")
    col_m3.metric("Totale CP 2026", fmt_eur(totale_cp))

    # --- Ricerca rapida ---
    search_q = st.text_input(
        "Cerca nei risultati",
        placeholder="es. infrastrutture, ferroviario, 7001 ...",
        key="search_cap",
    )
    if search_q:
        q = search_q.strip().upper()
        mask = (
            df_out["Capitolo di Spesa"].str.upper().str.contains(q, na=False)
            | df_out["Piano di Gestione"].str.upper().str.contains(q, na=False)
            | df_out["Numero Capitolo di Spesa"].astype(str).str.contains(q, na=False)
        )
        df_out = df_out[mask].copy()
        st.caption(
            f"**{df_out['Numero Capitolo di Spesa'].nunique()}** capitoli "
            f"corrispondenti a \"{search_q}\""
        )

    if df_out.empty:
        st.warning("Nessun risultato con i filtri selezionati.")
        st.stop()

    # --- Visualizzazione capitoli ---
    for amm in sorted(df_out["Amministrazione"].unique()):
        df_amm = df_out[df_out["Amministrazione"] == amm]
        st.markdown(
            f'<div class="mef-page-title" style="font-size:15px;margin-top:1.5rem">{amm}</div>',
            unsafe_allow_html=True,
        )

        for num_cap in sorted(df_amm["Numero Capitolo di Spesa"].unique()):
            df_cap = df_amm[df_amm["Numero Capitolo di Spesa"] == num_cap]
            nome_cap = df_cap["Capitolo di Spesa"].iloc[0]
            tot_cap = df_cap["Legge di Bilancio CP A1"].sum()

            with st.expander(
                f"Cap. {num_cap} -- {nome_cap}  |  {fmt_eur(tot_cap)}",
                expanded=False,
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Titolo:** {df_cap['Titolo'].iloc[0]}")
                    st.markdown(f"**Missione:** {df_cap['Missione'].iloc[0]}")
                with c2:
                    st.markdown(f"**Programma:** {df_cap['Programma'].iloc[0]}")
                    st.markdown(
                        f"**Centro Resp.:** "
                        f"{', '.join(df_cap[cdr_col].unique())}"
                    )

                display_cols = [
                    "Numero Piano di Gestione", "Piano di Gestione", "Azione",
                    "Legge di Bilancio CP A1", "Legge di Bilancio CP A2",
                    "Legge di Bilancio CP A3", "Legge di Bilancio CS A1",
                    "Legge di Bilancio RS A1",
                ]
                display_cols = [c for c in display_cols if c in df_cap.columns]
                df_display = (
                    df_cap[display_cols]
                    .copy()
                    .sort_values("Numero Piano di Gestione")
                )

                rename_map = {
                    "Numero Piano di Gestione": "N. PG",
                    "Piano di Gestione": "Descrizione PG",
                    "Azione": "Azione",
                    "Legge di Bilancio CP A1": "CP 2026",
                    "Legge di Bilancio CP A2": "CP 2027",
                    "Legge di Bilancio CP A3": "CP 2028",
                    "Legge di Bilancio CS A1": "CS 2026",
                    "Legge di Bilancio RS A1": "RS 2026",
                }
                df_display = df_display.rename(columns=rename_map)
                for col in ["CP 2026", "CP 2027", "CP 2028", "CS 2026", "RS 2026"]:
                    if col in df_display.columns:
                        df_display[col] = df_display[col].apply(fmt_eur)

                st.dataframe(df_display, use_container_width=True, hide_index=True)

                st.markdown(
                    f"**Totale Cap. {num_cap}:** "
                    f"CP 2026 = {fmt_eur(df_cap['Legge di Bilancio CP A1'].sum())} | "
                    f"CP 2027 = {fmt_eur(df_cap['Legge di Bilancio CP A2'].sum())} | "
                    f"CP 2028 = {fmt_eur(df_cap['Legge di Bilancio CP A3'].sum())}"
                )

    # ===================================================================
    #  EXPORT CSV + ASSEGNAZIONE UFFICIO
    # ===================================================================

    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)

    tab_csv, tab_ufficio = st.tabs(["Esporta CSV", "Assegna a Ufficio"])

    # --- Tab CSV ---
    with tab_csv:
        export_cols = [
            "Amministrazione", cdr_col,
            "Missione", "Programma", "Azione", "Titolo",
            "Numero Capitolo di Spesa", "Capitolo di Spesa",
            "Numero Piano di Gestione", "Piano di Gestione",
            "Categoria",
            "Legge di Bilancio CP A1", "Legge di Bilancio CP A2",
            "Legge di Bilancio CP A3", "Legge di Bilancio CS A1",
            "Legge di Bilancio CS A2", "Legge di Bilancio CS A3",
            "Legge di Bilancio RS A1",
        ]
        export_cols = [c for c in export_cols if c in df_out.columns]
        csv_data = (
            df_out[export_cols].to_csv(index=False, sep=";").encode("utf-8-sig")
        )
        st.download_button(
            label=f"Scarica CSV ({len(df_out):,} righe)",
            data=csv_data,
            file_name="bilancio_2026_selezione.csv",
            mime="text/csv",
        )

    # --- Tab Assegna Ufficio ---
    with tab_ufficio:
        st.markdown(
            "Assegna **tutti** i capitoli e PG visualizzati sopra a un ufficio."
        )

        col_uff, col_btn = st.columns([1, 2])

        with col_uff:
            if is_admin():
                # Il direttore puo assegnare a qualsiasi ufficio
                ufficio_sel = st.selectbox(
                    "Ufficio:",
                    options=["-- Seleziona --"] + [f"Ufficio {u}" for u in UFFICI],
                    key="ufficio_assegna",
                )
            else:
                # Gli altri possono assegnare solo al proprio ufficio
                proprio_ufficio = st.session_state.ufficio
                ufficio_sel = f"Ufficio {proprio_ufficio}"
                st.info(f"Assegnazione a: **{ufficio_sel}** (il tuo ufficio)")

        records = []
        for _, row in df_out.iterrows():
            records.append({
                "cap": int(row["Numero Capitolo di Spesa"]),
                "pg": int(row["Numero Piano di Gestione"]),
                "capitolo_spesa": row["Capitolo di Spesa"],
                "piano_gestione": row["Piano di Gestione"],
                "amministrazione": row["Amministrazione"],
                "centro_responsabilita": row[cdr_col],
                "missione": row["Missione"],
                "programma": row["Programma"],
                "azione": row["Azione"],
                "titolo": row["Titolo"],
                "cp_2026": int(row["Legge di Bilancio CP A1"]),
                "cp_2027": int(row["Legge di Bilancio CP A2"]),
                "cp_2028": int(row["Legge di Bilancio CP A3"]),
            })

        with col_btn:
            st.markdown("")
            st.markdown("")
            if ufficio_sel != "-- Seleziona --":
                ufficio_key = ufficio_sel.replace("Ufficio ", "")
                n_cap = df_out["Numero Capitolo di Spesa"].nunique()
                n_pg = len(df_out)

                if st.button(
                    f"Assegna {n_cap} capitoli / {n_pg} PG a {ufficio_sel}",
                    type="primary",
                    key="btn_assegna",
                ):
                    mappatura = load_mappatura()
                    mappatura[ufficio_key] = records
                    save_mappatura(mappatura)
                    st.success(
                        f"**{ufficio_sel}**: salvati **{n_cap}** capitoli e "
                        f"**{n_pg}** piani gestionali. "
                        f"(Mappatura precedente sovrascritta.)"
                    )
                    st.balloons()

        if ufficio_sel != "-- Seleziona --":
            ufficio_key = ufficio_sel.replace("Ufficio ", "")
            mappatura = load_mappatura()
            if ufficio_key in mappatura and mappatura[ufficio_key]:
                existing = mappatura[ufficio_key]
                caps_ex = len(set(r["cap"] for r in existing))
                st.info(
                    f"{ufficio_sel} ha attualmente **{caps_ex}** capitoli "
                    f"e **{len(existing)}** PG mappati. "
                    f"Premendo il pulsante verranno sostituiti."
                )

    # ===================================================================
    #  SIDEBAR -- Navigatore
    # ===================================================================

    with st.sidebar:
        st.markdown("---")
        st.header("Dataset")
        st.metric("Record totali", f"{len(df):,}")
        st.metric("Amministrazioni", f"{df['Amministrazione'].nunique()}")
        st.metric("Capitoli", f"{df['Numero Capitolo di Spesa'].nunique():,}")

        st.markdown("---")
        st.subheader("Filtri attivi")
        if sel_amm:
            for a in sel_amm:
                st.caption(a)
        if sel_cdr:
            for c in sel_cdr:
                st.caption(c)
        if sel_miss_labels:
            for m in sel_miss_labels:
                st.caption(m)
        if sel_prog_labels:
            for p in sel_prog_labels:
                st.caption(p)
        if sel_az_labels:
            for a in sel_az_labels:
                st.caption(a)

        st.markdown("---")
        st.caption(
            "Amministrazione > Centro Resp. > "
            "Missione > Programma > Azione > "
            "Capitolo > PG"
        )


# ==================================================================
#             PAGINA 2 -- MAPPATURA UFFICI
# ==================================================================

elif pagina == "Mappatura Uffici":

    st.markdown("""
    <div class="mef-page-title">Mappatura Uffici</div>
    <div class="mef-page-subtitle">
      Capitoli di spesa e piani gestionali assegnati a ciascun ufficio dell'ispettorato
    </div>
    """, unsafe_allow_html=True)

    mappatura = load_mappatura()

    if not mappatura:
        st.info(
            "Nessuna mappatura salvata. "
            "Vai alla pagina Navigatore e Selezione per assegnare "
            "capitoli e PG ai singoli uffici."
        )
        st.stop()

    # --- Riepilogo generale ---
    st.markdown('<div class="mef-page-title" style="font-size:17px">Riepilogo</div>', unsafe_allow_html=True)

    summary_rows = []
    for uff in UFFICI:
        items = mappatura.get(uff, [])
        if items:
            caps = len(set(r["cap"] for r in items))
            pg_count = len(items)
            tot_cp = sum(r.get("cp_2026", 0) for r in items)
            summary_rows.append({
                "Ufficio": f"Ufficio {uff}",
                "Capitoli": caps,
                "Piani Gestionali": pg_count,
                "Totale CP 2026": fmt_eur(tot_cp),
                "Stato": "Compilato",
            })
        else:
            summary_rows.append({
                "Ufficio": f"Ufficio {uff}",
                "Capitoli": 0,
                "Piani Gestionali": 0,
                "Totale CP 2026": "EUR 0",
                "Stato": "Da compilare",
            })

    df_summary = pd.DataFrame(summary_rows)
    compilati = sum(1 for r in summary_rows if r["Capitoli"] > 0)
    col_s1, col_s2 = st.columns(2)
    col_s1.metric("Uffici compilati", f"{compilati} / {len(UFFICI)}")
    col_s2.metric(
        "Totale PG mappati",
        f"{sum(r['Piani Gestionali'] for r in summary_rows):,}",
    )

    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # --- Dettaglio per ufficio ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">Dettaglio per Ufficio</div>', unsafe_allow_html=True)

    uffici_con_dati = [f"Ufficio {u}" for u in UFFICI if mappatura.get(u)]
    if not uffici_con_dati:
        st.info("Nessun ufficio ha ancora completato la mappatura.")
        st.stop()

    vista = st.radio(
        "Visualizza:",
        options=["Singolo ufficio", "Tutti gli uffici"],
        horizontal=True,
        key="vista_mappa",
    )

    uffici_da_mostrare = UFFICI
    if vista == "Singolo ufficio":
        sel_uff_det = st.selectbox(
            "Seleziona ufficio:", options=uffici_con_dati, key="det_uff"
        )
        uffici_da_mostrare = [sel_uff_det.replace("Ufficio ", "")]

    for uff in uffici_da_mostrare:
        items = mappatura.get(uff, [])
        if not items:
            continue

        df_uff = pd.DataFrame(items)
        caps = df_uff["cap"].nunique()
        pg_count = len(df_uff)
        tot_cp = df_uff["cp_2026"].sum() if "cp_2026" in df_uff.columns else 0

        with st.expander(
            f"Ufficio {uff} -- {caps} capitoli, {pg_count} PG, "
            f"CP 2026: {fmt_eur(tot_cp)}",
            expanded=(vista == "Singolo ufficio"),
        ):
            display_cols_map = {
                "cap": "N. Capitolo",
                "capitolo_spesa": "Capitolo di Spesa",
                "pg": "N. PG",
                "piano_gestione": "Piano di Gestione",
                "amministrazione": "Amministrazione",
                "centro_responsabilita": "Centro Responsabilita",
                "missione": "Missione",
                "programma": "Programma",
                "azione": "Azione",
                "cp_2026": "CP 2026",
                "cp_2027": "CP 2027",
                "cp_2028": "CP 2028",
            }
            cols_present = [c for c in display_cols_map if c in df_uff.columns]
            df_show = df_uff[cols_present].copy()
            df_show = df_show.rename(
                columns={c: display_cols_map[c] for c in cols_present}
            )
            df_show = df_show.sort_values(
                ["N. Capitolo", "N. PG"]
            ).reset_index(drop=True)

            for col in ["CP 2026", "CP 2027", "CP 2028"]:
                if col in df_show.columns:
                    df_show[col] = df_show[col].apply(fmt_eur)

            st.dataframe(df_show, use_container_width=True, hide_index=True)

            csv_uff = df_show.to_csv(index=False, sep=";").encode("utf-8-sig")
            st.download_button(
                label=f"Scarica CSV Ufficio {uff}",
                data=csv_uff,
                file_name=f"mappatura_ufficio_{uff}.csv",
                mime="text/csv",
                key=f"dl_uff_{uff}",
            )

    # --- Matrice Cap x Ufficio ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">Matrice Capitoli x Uffici</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="mef-page-subtitle">Quali uffici sono competenti su ciascun capitolo? '
        'Utile per individuare sovrapposizioni.</div>',
        unsafe_allow_html=True,
    )

    all_caps = set()
    cap_names = {}
    for uff in UFFICI:
        for item in mappatura.get(uff, []):
            cap = item["cap"]
            all_caps.add(cap)
            cap_names[cap] = item.get("capitolo_spesa", str(cap))

    if all_caps:
        matrix_rows = []
        for cap in sorted(all_caps):
            row = {"Capitolo": cap, "Descrizione": cap_names.get(cap, "")}
            for uff in UFFICI:
                items_uff = mappatura.get(uff, [])
                caps_uff = set(r["cap"] for r in items_uff)
                row[f"Uff. {uff}"] = "V" if cap in caps_uff else ""
            matrix_rows.append(row)

        df_matrix = pd.DataFrame(matrix_rows)
        st.dataframe(df_matrix, use_container_width=True, hide_index=True)

        csv_matrix = df_matrix.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="Scarica matrice Cap x Uffici (CSV)",
            data=csv_matrix,
            file_name="matrice_capitoli_uffici.csv",
            mime="text/csv",
            key="dl_matrice",
        )
    else:
        st.info("Nessun capitolo mappato.")

    # --- Export completo ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">Export completo mappatura</div>', unsafe_allow_html=True)

    all_rows = []
    for uff in UFFICI:
        for item in mappatura.get(uff, []):
            row = {"Ufficio": f"Ufficio {uff}"}
            row.update(item)
            all_rows.append(row)

    if all_rows:
        df_all = pd.DataFrame(all_rows)
        csv_all = df_all.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label=f"Scarica mappatura completa ({len(df_all):,} righe)",
            data=csv_all,
            file_name="mappatura_completa_uffici.csv",
            mime="text/csv",
            key="dl_all",
        )

    # --- Reset singolo ufficio ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">Resetta mappatura ufficio</div>', unsafe_allow_html=True)

    col_r1, col_r2 = st.columns([1, 2])
    with col_r1:
        if is_admin():
            uff_reset = st.selectbox(
                "Ufficio da resettare:",
                options=["-- Seleziona --"] + [f"Ufficio {u}" for u in UFFICI],
                key="uff_reset",
            )
        else:
            proprio_ufficio = st.session_state.ufficio
            uff_reset = f"Ufficio {proprio_ufficio}"
            st.info(f"Puoi resettare solo: **{uff_reset}**")

    with col_r2:
        st.markdown("")
        st.markdown("")
        if uff_reset != "-- Seleziona --":
            uff_key = uff_reset.replace("Ufficio ", "")
            if mappatura.get(uff_key):
                if st.button(
                    f"Cancella mappatura {uff_reset}",
                    key="btn_reset",
                ):
                    mappatura[uff_key] = []
                    save_mappatura(mappatura)
                    st.success(f"Mappatura di {uff_reset} cancellata.")
                    st.rerun()
            else:
                st.caption(f"{uff_reset} non ha mappature.")

    # --- SIDEBAR -- Mappatura ---
    with st.sidebar:
        st.markdown("---")
        st.header("Stato compilazione")
        for uff in UFFICI:
            items = mappatura.get(uff, [])
            if items:
                caps = len(set(r["cap"] for r in items))
                st.caption(f"Uff. {uff}: {caps} cap., {len(items)} PG")
            else:
                st.caption(f"Uff. {uff}: da compilare")


# ===================================================================
#  SIDEBAR -- INFO UTENTE E ADMIN (comune a tutte le pagine)
# ===================================================================

with st.sidebar:
    st.markdown("---")
    st.header("Utente connesso")
    st.markdown(f"**{st.session_state.nominativo}**")
    st.caption(f"Ufficio: {st.session_state.ufficio}")
    st.caption(f"Ruolo: {st.session_state.ruolo}")
    st.caption(f"Email: {st.session_state.email}")

    if st.button("Logout"):
        auth.logout()
        st.rerun()

    # Pannello admin
    if is_admin():
        st.markdown("---")
        pannello_admin()


# ===================================================================
#  FOOTER
# ===================================================================

st.markdown(
    f'<div class="mef-footer">'
    f'  <span>Ministero dell\'Economia e delle Finanze -- Ragioneria Generale dello Stato</span>'
    f'  <span>Avviato: {start_time_str} &nbsp;|&nbsp; Legge di Bilancio 2026</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ===================================================================
#  SIDEBAR FOOTER (comune)
# ===================================================================

with st.sidebar:
    st.markdown("---")
    st.markdown(
        f"<div style='padding:14px 0 8px 0;font-size:14px;font-weight:700;"
        f"color:#FFFFFF;font-family:Segoe UI,sans-serif;"
        f"border-bottom:1px solid rgba(255,255,255,.15);margin-bottom:4px'>"
        f"MEF &nbsp;<span style='color:#C49B1D'>&#183;</span>&nbsp; RGS"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-size:10px;opacity:.40;padding-bottom:8px;"
        f"font-family:Segoe UI,sans-serif'>"
        f"Avviato: {start_time_str}<br>"
        f"Fonte: RGS -- Legge di Bilancio 2026"
        f"</div>",
        unsafe_allow_html=True,
    )
