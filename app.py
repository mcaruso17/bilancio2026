import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from auth import Authenticator
from permissions import puo_modificare, puo_visualizzare, is_admin, is_super_admin
from database import init_database, get_connection
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from load_users import genera_email, genera_password

start_time = datetime.now()
start_time_str = start_time.strftime("%d/%m/%Y %H:%M:%S")

# ======================================================================
#                    IMPOSTAZIONI DA MODIFICARE
# ======================================================================

BILANCIO_CSV = "bilanci.csv.gz"
MAPPATURA_FILE = "mappatura_uffici.json"
PERSONALE_XLSX = "personale.xlsx"
CREDENZIALI_CSV = "credenziali_temporanee.csv"

UFFICI = [
    "1", "2", "3", "4", "5", "6", "7",
    "8", "9", "10", "11", "12", "13", "CRS I", "CRS II"
]

# ======================================================================
#          FINE IMPOSTAZIONI - DA QUI IN GIU NON TOCCARE
# ======================================================================

init_database()
auth = Authenticator()

# ===================================================================
#  AUTO-CARICAMENTO UTENTI DA REPO (personale.xlsx + credenziali_temporanee.csv)
# ===================================================================

def auto_carica_utenti():
    """Carica utenti dal file personale.xlsx e credenziali_temporanee.csv
    presenti nella repo. Eseguito a ogni avvio per ricostruire il DB."""
    if not os.path.exists(PERSONALE_XLSX) or not os.path.exists(CREDENZIALI_CSV):
        return

    try:
        df_pers = pd.read_excel(PERSONALE_XLSX)
        df_pers.columns = df_pers.columns.str.strip().str.lower()
        df_pers = df_pers.dropna(subset=["nominativo"])

        df_cred = pd.read_csv(CREDENZIALI_CSV)
        df_cred.columns = df_cred.columns.str.strip().str.lower()

        # Crea lookup email -> password dal file credenziali
        cred_lookup = {}
        for _, r in df_cred.iterrows():
            cred_lookup[str(r["email"]).strip().lower()] = str(r["password"]).strip()
            # Anche per nominativo come fallback
            cred_lookup[str(r["nominativo"]).strip().lower()] = str(r["password"]).strip()

        with get_connection() as conn:
            for _, riga in df_pers.iterrows():
                nominativo = str(riga["nominativo"]).strip()
                email = genera_email(nominativo)

                # Cerca la password: prima per email, poi per nominativo
                password_utente = cred_lookup.get(
                    email.lower(),
                    cred_lookup.get(nominativo.lower(), None)
                )
                if not password_utente:
                    continue  # Salta se non trova la password

                pw_hash, salt = Authenticator.hash_password(password_utente)
                stored = f"{pw_hash}:{salt}"

                # Controlla se l'utente ha gia cambiato password (non sovrascrivere)
                existing = conn.execute(
                    "SELECT deve_cambiare_password FROM users WHERE email = ?",
                    (email,)
                ).fetchone()

                if existing and existing["deve_cambiare_password"] == 0:
                    # L'utente ha gia cambiato password, aggiorna solo i dati anagrafici
                    conn.execute(
                        """UPDATE users SET
                            nominativo = ?, ruolo = ?, ufficio = ?,
                            stanza = ?, interno = ?, cellulare = ?
                        WHERE email = ?""",
                        (
                            nominativo,
                            str(riga.get("ruolo", "")),
                            str(riga.get("ufficio", "")),
                            str(riga.get("stanza", "")),
                            str(riga.get("interno", "")),
                            str(riga.get("cellulare", "")),
                            email,
                        )
                    )
                else:
                    # Utente nuovo o che non ha ancora cambiato password: imposta tutto
                    conn.execute(
                        """INSERT INTO users
                        (nominativo, email, password_hash, ruolo, ufficio,
                         stanza, interno, cellulare, deve_cambiare_password)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                        ON CONFLICT(email) DO UPDATE SET
                            nominativo = excluded.nominativo,
                            password_hash = excluded.password_hash,
                            ruolo = excluded.ruolo,
                            ufficio = excluded.ufficio,
                            stanza = excluded.stanza,
                            interno = excluded.interno,
                            cellulare = excluded.cellulare,
                            deve_cambiare_password = 1""",
                        (
                            nominativo, email, stored,
                            str(riga.get("ruolo", "")),
                            str(riga.get("ufficio", "")),
                            str(riga.get("stanza", "")),
                            str(riga.get("interno", "")),
                            str(riga.get("cellulare", "")),
                        )
                    )
    except Exception as e:
        pass  # Silenzioso all'avvio, non bloccare l'app

auto_carica_utenti()

st.set_page_config(
    page_title="Navigatore LdB -- Ragioneria Generale dello Stato",
    layout="wide",
    initial_sidebar_state="expanded",
)

MEF_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@300;400;600;700&display=swap');

:root {
    --mef-blue:       #1D3D8F;
    --mef-blue-dark:  #132B6B;
    --mef-blue-light: #E8EDF7;
    --mef-gold:       #C49B1D;
    --mef-border:     #CED5E8;
    --font: 'Segoe UI', 'Source Sans 3', sans-serif;
}

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
[data-theme="dark"] [data-testid="stSidebar"],
[data-theme="dark"] [data-testid="stSidebar"] * {
    background-color: #132B6B !important;
    color: rgba(255,255,255,0.82) !important;
}
[data-theme="dark"] [data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #FFFFFF !important;
}

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

.mef-tag {
    display: inline-block; padding: 2px 7px; border-radius: 2px;
    font-size: 10px; font-weight: 700; letter-spacing: .07em;
    text-transform: uppercase; font-family: var(--font); line-height: 1.6;
}
.tag-nav { background-color: #1D3D8F; color: #FFFFFF; }
.tag-map { background-color: #C49B1D; color: #FFFFFF; }

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

.stSelectbox > label {
    font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: .07em !important;
    color: #556080 !important; font-family: var(--font) !important;
}
.stSelectbox [data-baseweb="select"] div {
    background-color: #FFFFFF !important; color: #17203A !important;
}

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

.stButton > button,
.stDownloadButton > button {
    background-color: #1D3D8F !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 3px !important;
    font-family: var(--font) !important;
    font-weight: 600 !important;
    letter-spacing: .03em !important;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    background-color: #132B6B !important;
}

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
[data-testid="stSidebar"] .streamlit-expanderHeader,
[data-testid="stSidebar"] details summary {
    background-color: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.15) !important;
    color: rgba(255,255,255,0.82) !important;
}
[data-testid="stSidebar"] .streamlit-expanderContent,
[data-testid="stSidebar"] details > div {
    background-color: rgba(255,255,255,0.05) !important;
    border-color: rgba(255,255,255,0.15) !important;
    color: rgba(255,255,255,0.82) !important;
}
[data-testid="stSidebar"] .stRadio label {
    color: rgba(255,255,255,.82) !important;
    font-size: 13px !important;
}
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] div {
    background-color: transparent !important;
}

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
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

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

#MainMenu                              { display: none !important; }
footer                                 { display: none !important; }
[data-testid="stToolbar"]             { display: none !important; }
[data-testid="stDecoration"]          { display: none !important; }
[data-testid="stStatusWidget"]        { display: none !important; }

.mef-footer {
    border-top: 1px solid #CED5E8; margin-top: 3rem; padding-top: 1rem;
    font-size: 11px; color: #556080; font-family: var(--font);
    display: flex; justify-content: space-between;
    flex-wrap: wrap; gap: 4px; background-color: #FFFFFF;
}

/* Badge per confronto annuale */
.badge-new { background:#27AE60; color:#FFF; padding:2px 7px; border-radius:2px; font-size:10px; font-weight:700; letter-spacing:.05em; }
.badge-gone { background:#CC2222; color:#FFF; padding:2px 7px; border-radius:2px; font-size:10px; font-weight:700; letter-spacing:.05em; }
.badge-up { color:#27AE60; font-weight:700; }
.badge-down { color:#CC2222; font-weight:700; }
.badge-flat { color:#556080; font-weight:600; }
</style>
"""

st.markdown(MEF_CSS, unsafe_allow_html=True)


# ===================================================================
#  AUTENTICAZIONE
# ===================================================================

def pagina_login():
    st.markdown("""
    <div class="mef-header">
      <div class="mef-header-inner">
        <div>
          <div class="mef-header-ministry">Ministero dell'Economia e delle Finanze</div>
          <div class="mef-header-dept">Ragioneria Generale dello Stato</div>
          <div class="mef-header-sub">Navigatore Legge di Bilancio</div>
        </div>
        <div class="mef-header-right">
          <div class="mef-app-name">LdB 2011-2026</div>
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
    st.markdown('<div class="mef-page-title">Caricamento Utenti</div>', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-subtitle">Area riservata all\'amministratore del sistema</div>', unsafe_allow_html=True)

    # Mostra stato auto-caricamento
    has_personale = os.path.exists(PERSONALE_XLSX)
    has_credenziali = os.path.exists(CREDENZIALI_CSV)

    if has_personale and has_credenziali:
        st.success(
            f"**Caricamento automatico attivo.** "
            f"I file `{PERSONALE_XLSX}` e `{CREDENZIALI_CSV}` sono presenti nella repo. "
            f"Gli utenti vengono caricati automaticamente a ogni avvio dell'app."
        )
        with get_connection() as conn:
            n_utenti = conn.execute("SELECT COUNT(*) FROM users WHERE attivo = 1").fetchone()[0]
        st.info(f"Utenti attivi nel database: **{n_utenti}**")
    else:
        missing = []
        if not has_personale:
            missing.append(f"`{PERSONALE_XLSX}`")
        if not has_credenziali:
            missing.append(f"`{CREDENZIALI_CSV}`")
        st.warning(f"File mancanti nella repo: {', '.join(missing)}. Caricamento automatico non attivo.")

    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown("**Caricamento manuale** (opzionale, per aggiungere utenti extra)")

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
                        """INSERT INTO users
                        (nominativo, email, password_hash, ruolo, ufficio, stanza, interno, cellulare, deve_cambiare_password)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                        ON CONFLICT(email) DO UPDATE SET
                            password_hash = excluded.password_hash,
                            ruolo = excluded.ruolo,
                            ufficio = excluded.ufficio,
                            stanza = excluded.stanza,
                            interno = excluded.interno,
                            cellulare = excluded.cellulare,
                            deve_cambiare_password = 1""",
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
    st.header("Gestione Utenti")
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, nominativo, email FROM users WHERE attivo = 1"
        ).fetchall()
        utenti = [dict(r) for r in rows]

    utente_scelto = st.selectbox(
        "Seleziona utente",
        utenti,
        format_func=lambda u: f"{u['nominativo']} ({u['email']})",
        key="sel_utente_reset",
    )

    if st.button("Reset Password", key="btn_reset_pw"):
        # Cerca la password originale dal file credenziali
        nuova_pw = None
        if os.path.exists(CREDENZIALI_CSV):
            try:
                df_cred = pd.read_csv(CREDENZIALI_CSV)
                df_cred.columns = df_cred.columns.str.strip().str.lower()
                match = df_cred[
                    df_cred["email"].str.strip().str.lower()
                    == utente_scelto["email"].strip().lower()
                ]
                if match.empty:
                    match = df_cred[
                        df_cred["nominativo"].str.strip().str.lower()
                        == utente_scelto["nominativo"].strip().lower()
                    ]
                if not match.empty:
                    nuova_pw = str(match.iloc[0]["password"]).strip()
            except Exception:
                pass

        if nuova_pw:
            pw_hash, salt = Authenticator.hash_password(nuova_pw)
            stored = f"{pw_hash}:{salt}"
            with get_connection() as conn:
                conn.execute(
                    "UPDATE users SET password_hash = ?, deve_cambiare_password = 1 WHERE id = ?",
                    (stored, utente_scelto["id"])
                )
            st.success(f"Password resettata a quella originale.")
            st.warning("L'utente dovra cambiarla al prossimo accesso.")
        else:
            nuova_pw = Authenticator.reset_password(utente_scelto["id"])
            st.success(f"Nuova pw casuale: {nuova_pw}")
            st.warning("Comunicala all'utente!")

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
#  SIDEBAR -- NAVIGAZIONE + INFO UTENTE (sempre visibili)
# ===================================================================

with st.sidebar:
    pagina = st.radio(
        "Pagina",
        options=[
            "Cerca Piano Gestionale",
            "Confronto Annuale",
            "Mappatura Uffici",
        ],
        index=0,
    )

    st.markdown("---")
    st.header("Utente connesso")
    st.markdown(f"**{st.session_state.nominativo}**")
    st.caption(f"Ufficio: {st.session_state.ufficio}")
    st.caption(f"Ruolo: {st.session_state.ruolo}")
    st.caption(f"Email: {st.session_state.email}")
    if is_super_admin():
        st.caption("**SUPER ADMIN**")

    if st.button("Logout"):
        for key in ["authenticated", "user_id", "nominativo", "email",
                     "ruolo", "ufficio", "deve_cambiare_password"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    if is_super_admin():
        st.markdown("---")
        pannello_admin()



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
      <div class="mef-app-name">LdB 2011-2026</div>
      <div class="mef-app-tagline">Navigatore e Mappatura Uffici</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ===================================================================
#  CARICAMENTO DATI
# ===================================================================

ANNO_COL = "Esercizio Finanziario"

@st.cache_data
def load_bilancio():
    if not os.path.exists(BILANCIO_CSV):
        return pd.DataFrame()
    df = pd.read_csv(BILANCIO_CSV, sep=";", encoding="utf-8-sig", low_memory=False)
    str_cols = df.select_dtypes(include="object").columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
    # Converti colonna anno in intero
    if ANNO_COL in df.columns:
        df[ANNO_COL] = pd.to_numeric(df[ANNO_COL], errors="coerce").fillna(0).astype(int)
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


def fmt_eur(val):
    if pd.isna(val) or val == 0:
        return "EUR 0"
    return f"EUR {int(val):,.0f}".replace(",", ".")


def fmt_var(val):
    """Formatta una variazione con segno e colore"""
    if pd.isna(val) or val == 0:
        return '<span class="badge-flat">--</span>'
    sign = "+" if val > 0 else ""
    css = "badge-up" if val > 0 else "badge-down"
    return f'<span class="{css}">{sign}{int(val):,.0f}</span>'.replace(",", ".")


def fmt_pct(val):
    """Formatta una variazione percentuale"""
    if pd.isna(val):
        return '<span class="badge-flat">n/a</span>'
    if val == float("inf") or val == float("-inf"):
        return '<span class="badge-up">NUOVO</span>' if val > 0 else '<span class="badge-down">AZZERATO</span>'
    sign = "+" if val > 0 else ""
    css = "badge-up" if val > 0 else ("badge-down" if val < 0 else "badge-flat")
    return f'<span class="{css}">{sign}{val:.1f}%</span>'


def build_label_map(df_slice, code_col, name_col):
    pairs = (
        df_slice[[code_col, name_col]]
        .drop_duplicates()
        .sort_values(code_col)
    )

    def fmt_code(val):
        try:
            return f"{int(val):02d}"
        except (ValueError, TypeError):
            return str(val).strip()

    labels = [
        f"{fmt_code(row[code_col])} -- {row[name_col]}"
        for _, row in pairs.iterrows()
    ]
    label_to_code = {
        f"{fmt_code(row[code_col])} -- {row[name_col]}": row[code_col]
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

# Lista anni disponibili
anni_disponibili = sorted(df[ANNO_COL].unique())
anno_max = max(anni_disponibili)

st.markdown(f"""
<div class="mef-page-title">Legge di Bilancio {anni_disponibili[0]}-{anno_max}</div>
<div class="mef-page-subtitle">
  Navigazione gerarchica del bilancio, confronto annuale e mappatura uffici ispettorato
</div>
<div class="mef-status-row">
  <div class="mef-status-card">
    <div class="mef-status-dot"></div>
    <span>Dataset: <strong>{len(df):,}</strong> record --
    <strong>{df['Numero Capitolo di Spesa'].nunique():,}</strong> capitoli --
    <strong>{len(anni_disponibili)}</strong> esercizi ({anni_disponibili[0]}-{anno_max})</span>
    <span class="mef-status-tag">LdB</span>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)

# Identifica colonna CDR una volta sola
cdr_col = "Centro Responsabilita" if "Centro Responsabilita" in df.columns else "Centro Responsabilit\u00e0"


# ==================================================================
#     FUNZIONE COMUNE: VISUALIZZA CAPITOLI (usata da entrambe le ricerche)
# ==================================================================

def visualizza_capitoli(df_out, mostra_selezione=False):
    """Mostra i capitoli con expander e metriche.
    Se mostra_selezione=True, aggiunge checkbox per selezionare i capitoli
    e restituisce la lista dei numeri capitolo selezionati."""
    n_cap_out = df_out["Numero Capitolo di Spesa"].nunique()
    n_pg_out = len(df_out)
    totale_cp = df_out["Legge di Bilancio CP A1"].sum()

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Capitoli di Spesa", f"{n_cap_out:,}")
    col_m2.metric("Piani Gestionali", f"{n_pg_out:,}")
    col_m3.metric("Totale CP Anno 1", fmt_eur(totale_cp))

    # --- Pulsanti Seleziona/Deseleziona tutti ---
    user_ruolo = st.session_state.get("ruolo", "")
    user_puo_mappare = mostra_selezione and (is_super_admin() or user_ruolo in ["DIR.", "FUN."])

    all_caps = sorted(df_out["Numero Capitolo di Spesa"].unique())

    if user_puo_mappare:
        col_sel, col_desel, col_spacer = st.columns([1, 1, 3])
        with col_sel:
            if st.button("Seleziona tutti", key="btn_sel_tutti"):
                for cap in all_caps:
                    st.session_state[f"chk_cap_{cap}"] = True
                st.rerun()
        with col_desel:
            if st.button("Deseleziona tutti", key="btn_desel_tutti"):
                for cap in all_caps:
                    st.session_state[f"chk_cap_{cap}"] = False
                st.rerun()

    caps_selezionati = []

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

            # Checkbox + Expander sulla stessa riga
            if user_puo_mappare:
                col_chk, col_exp = st.columns([0.05, 0.95])
                with col_chk:
                    checked = st.checkbox(
                        "sel",
                        value=st.session_state.get(f"chk_cap_{num_cap}", False),
                        key=f"chk_cap_{num_cap}",
                        label_visibility="collapsed",
                    )
                    if checked:
                        caps_selezionati.append(num_cap)
                container = col_exp
            else:
                container = st.container()

            with container:
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
                        "Legge di Bilancio CP A1": "CP Anno 1",
                        "Legge di Bilancio CP A2": "CP Anno 2",
                        "Legge di Bilancio CP A3": "CP Anno 3",
                        "Legge di Bilancio CS A1": "CS Anno 1",
                        "Legge di Bilancio RS A1": "RS Anno 1",
                    }
                    df_display = df_display.rename(columns=rename_map)
                    for col in ["CP Anno 1", "CP Anno 2", "CP Anno 3", "CS Anno 1", "RS Anno 1"]:
                        if col in df_display.columns:
                            df_display[col] = df_display[col].apply(fmt_eur)

                    st.dataframe(df_display, use_container_width=True, hide_index=True)

                    st.markdown(
                        f"**Totale Cap. {num_cap}:** "
                        f"CP A1 = {fmt_eur(df_cap['Legge di Bilancio CP A1'].sum())} | "
                        f"CP A2 = {fmt_eur(df_cap['Legge di Bilancio CP A2'].sum())} | "
                        f"CP A3 = {fmt_eur(df_cap['Legge di Bilancio CP A3'].sum())}"
                    )

    return caps_selezionati


def sezione_export_e_assegnazione(df_out, caps_selezionati=None):
    """Mostra le tab di export CSV e assegnazione ufficio.
    caps_selezionati: lista di numeri capitolo scelti dall'utente via checkbox."""
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)

    user_ruolo = st.session_state.ruolo
    user_puo_mappare = is_super_admin() or user_ruolo in ["DIR.", "FUN."]

    if user_puo_mappare:
        tab_csv, tab_ufficio = st.tabs(["Esporta CSV", "Assegna a Ufficio"])
    else:
        tab_csv = st.tabs(["Esporta CSV"])[0]

    with tab_csv:
        export_cols = [
            ANNO_COL, "Amministrazione", cdr_col,
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
            file_name="bilancio_selezione.csv",
            mime="text/csv",
        )

    if user_puo_mappare:
        with tab_ufficio:
            if not caps_selezionati:
                st.info(
                    "Seleziona almeno un capitolo usando le checkbox accanto ai risultati, "
                    "oppure clicca **Seleziona tutti**."
                )
            else:
                df_assegna = df_out[
                    df_out["Numero Capitolo di Spesa"].isin(caps_selezionati)
                ].copy()

                n_cap = len(caps_selezionati)
                n_pg = len(df_assegna)
                st.success(f"**{n_cap}** capitoli selezionati ({n_pg} PG)")

                col_uff, col_btn = st.columns([1, 2])

                with col_uff:
                    if is_super_admin():
                        ufficio_sel = st.selectbox(
                            "Ufficio:",
                            options=["-- Seleziona --"] + [f"Ufficio {u}" for u in UFFICI],
                            key="ufficio_assegna",
                        )
                    else:
                        proprio_ufficio = st.session_state.ufficio
                        ufficio_sel = f"Ufficio {proprio_ufficio}"
                        st.info(f"Assegnazione a: **{ufficio_sel}** (il tuo ufficio)")

                records = []
                for _, row in df_assegna.iterrows():
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

                        if st.button(
                            f"Aggiungi {n_cap} capitoli / {n_pg} PG a {ufficio_sel}",
                            type="primary",
                            key="btn_assegna",
                        ):
                            mappatura = load_mappatura()
                            esistenti = mappatura.get(ufficio_key, [])
                            chiavi_esistenti = {(r["cap"], r["pg"]) for r in esistenti}
                            nuovi = [r for r in records if (r["cap"], r["pg"]) not in chiavi_esistenti]
                            mappatura[ufficio_key] = esistenti + nuovi
                            save_mappatura(mappatura)
                            st.success(
                                f"**{ufficio_sel}**: aggiunti **{len(nuovi)}** nuovi PG "
                                f"(su {n_pg} selezionati, {n_pg - len(nuovi)} gia presenti)."
                            )

                if ufficio_sel != "-- Seleziona --":
                    ufficio_key = ufficio_sel.replace("Ufficio ", "")
                    mappatura = load_mappatura()
                    if ufficio_key in mappatura and mappatura[ufficio_key]:
                        existing = mappatura[ufficio_key]
                        caps_ex = len(set(r["cap"] for r in existing))
                        st.info(
                            f"{ufficio_sel} ha attualmente **{caps_ex}** capitoli "
                            f"e **{len(existing)}** PG mappati. "
                            f"I nuovi verranno aggiunti senza cancellare i precedenti."
                        )


# ==================================================================
#     WIDGET SELEZIONE ANNO (usato nelle pagine di ricerca)
# ==================================================================

def selettore_anno(key_prefix=""):
    """Mostra il selettore anno e restituisce il df filtrato per l'anno scelto"""
    st.markdown(
        '<div class="mef-page-title" style="font-size:17px">Esercizio Finanziario</div>',
        unsafe_allow_html=True,
    )
    anno_sel = st.selectbox(
        "Seleziona l'anno di bilancio:",
        options=sorted(anni_disponibili, reverse=True),
        index=0,
        key=f"{key_prefix}_anno",
    )
    df_anno = df[df[ANNO_COL] == anno_sel].copy()
    st.caption(f"Esercizio **{anno_sel}**: {len(df_anno):,} record, "
               f"{df_anno['Numero Capitolo di Spesa'].nunique():,} capitoli")
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    return anno_sel, df_anno


# ==================================================================
#         PAGINA UNICA -- CERCA PIANO GESTIONALE
# ==================================================================

if pagina == "Cerca Piano Gestionale":

    anno_sel, df_anno = selettore_anno("cerca")

    # --- RICERCA TESTUALE (sempre visibile, prominente) ---
    st.markdown(
        '<div class="mef-page-title" style="font-size:17px">Ricerca testuale</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="mef-page-subtitle">'
        'Cerca per descrizione del capitolo, del piano gestionale o per numero. '
        'I risultati appaiono man mano che digiti.'
        '</div>',
        unsafe_allow_html=True,
    )

    search_cap_text = st.text_input(
        "Cerca Capitolo di Spesa:",
        placeholder="es. ferroviario, infrastrutture, 7001 ...",
        key="search_cap_text",
    )

    search_pg_text = st.text_input(
        "Cerca Piano di Gestione:",
        placeholder="es. manutenzione, contributi, personale ...",
        key="search_pg_text",
    )

    # --- FILTRI A CASCATA (tutti opzionali, in expander) ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)

    # Pulsante Reset
    col_filtri_label, col_filtri_reset = st.columns([4, 1])
    with col_filtri_reset:
        if st.button("Reset filtri", key="btn_reset_filtri"):
            keys_to_clear = ["sel_titolo", "sel_amm", "sel_cdr", "sel_miss",
                             "sel_prog", "sel_azione", "search_cap_num",
                             "search_cap_text", "search_pg_text",
                             "filtro_amm_risultati"]
            # Pulisci anche tutte le checkbox capitoli
            for k in list(st.session_state.keys()):
                if k.startswith("chk_cap_"):
                    keys_to_clear.append(k)
            for k in keys_to_clear:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    df_filtered = df_anno.copy()

    # Variabili per tracciare i filtri attivi (per la sidebar)
    filtri_attivi = []

    with st.expander("Filtri avanzati (opzionali)", expanded=False):
        st.caption("Tutti i filtri sono opzionali. Ogni selezione restringe le opzioni successive.")

        # --- TITOLO ---
        titoli = sorted(df_filtered["Titolo"].unique())
        sel_titoli = st.multiselect(
            "Titolo:",
            options=titoli,
            key="sel_titolo",
        )
        if sel_titoli:
            df_filtered = df_filtered[df_filtered["Titolo"].isin(sel_titoli)].copy()
            filtri_attivi.append(("Titolo", sel_titoli))

        # --- AMMINISTRAZIONE ---
        amministrazioni = sorted(df_filtered["Amministrazione"].unique())
        sel_amm = st.multiselect(
            "Amministrazione:",
            options=amministrazioni,
            key="sel_amm",
        )
        if sel_amm:
            df_filtered = df_filtered[df_filtered["Amministrazione"].isin(sel_amm)].copy()
            filtri_attivi.append(("Amministrazione", sel_amm))

        # --- CENTRO RESPONSABILITA ---
        cdr_options = sorted(df_filtered[cdr_col].unique())
        sel_cdr = st.multiselect(
            "Centro Responsabilita (Dipartimento):",
            options=cdr_options,
            key="sel_cdr",
        )
        if sel_cdr:
            df_filtered = df_filtered[df_filtered[cdr_col].isin(sel_cdr)].copy()
            filtri_attivi.append(("Centro Resp.", sel_cdr))

        # --- MISSIONE ---
        miss_labels, miss_map = build_label_map(df_filtered, "Codice Missione", "Missione")
        sel_miss_labels = st.multiselect(
            "Missione:",
            options=miss_labels,
            key="sel_miss",
        )
        if sel_miss_labels:
            sel_miss_codes = [miss_map[l] for l in sel_miss_labels]
            df_filtered = df_filtered[df_filtered["Codice Missione"].isin(sel_miss_codes)].copy()
            filtri_attivi.append(("Missione", sel_miss_labels))

        # --- PROGRAMMA ---
        prog_labels, prog_map = build_label_map(df_filtered, "Codice Programma", "Programma")
        sel_prog_labels = st.multiselect(
            "Programma:",
            options=prog_labels,
            key="sel_prog",
        )
        if sel_prog_labels:
            sel_prog_codes = [prog_map[l] for l in sel_prog_labels]
            df_filtered = df_filtered[df_filtered["Codice Programma"].isin(sel_prog_codes)].copy()
            filtri_attivi.append(("Programma", sel_prog_labels))

        # --- AZIONE ---
        az_labels, az_map = build_label_map(df_filtered, "Codice Azione", "Azione")
        sel_az_labels = st.multiselect(
            "Azione:",
            options=az_labels,
            key="sel_azione",
        )
        if sel_az_labels:
            sel_az_codes = [az_map[l] for l in sel_az_labels]
            df_filtered = df_filtered[df_filtered["Codice Azione"].isin(sel_az_codes)].copy()
            filtri_attivi.append(("Azione", sel_az_labels))

        # --- NUMERO CAPITOLO DIRETTO ---
        search_cap_num = st.text_input(
            "Numeri capitolo (separati da virgola):",
            placeholder="es. 7001, 7002, 1320",
            key="search_cap_num",
        )
        if search_cap_num:
            numeri_cercati = []
            for n in search_cap_num.split(","):
                n = n.strip()
                if n.isdigit():
                    numeri_cercati.append(int(n))
            if numeri_cercati:
                df_filtered = df_filtered[
                    df_filtered["Numero Capitolo di Spesa"].isin(numeri_cercati)
                ].copy()
                filtri_attivi.append(("N. Capitolo", [str(n) for n in numeri_cercati]))

    # --- APPLICA RICERCA TESTUALE ---
    df_out = df_filtered.copy()

    if search_cap_text:
        q = search_cap_text.strip().lower()
        mask = (
            df_out["Capitolo di Spesa"].str.lower().str.contains(q, na=False)
            | df_out["Numero Capitolo di Spesa"].astype(str).str.contains(q, na=False)
        )
        df_out = df_out[mask].copy()

    if search_pg_text:
        q = search_pg_text.strip().lower()
        df_out = df_out[
            df_out["Piano di Gestione"].str.lower().str.contains(q, na=False)
        ].copy()

    # --- CONTEGGIO E AVVISO ---
    has_any_filter = bool(search_cap_text) or bool(search_pg_text) or bool(filtri_attivi)

    if not has_any_filter:
        st.info(
            "Usa la barra di ricerca testuale oppure apri i **Filtri avanzati** "
            "per restringere i risultati."
        )
        st.stop()

    if df_out.empty:
        st.warning("Nessun risultato con i filtri selezionati.")
        st.stop()

    # --- RISULTATI ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown(
        '<div class="mef-page-title" style="font-size:17px">Risultati</div>',
        unsafe_allow_html=True,
    )

    n_cap_out = df_out["Numero Capitolo di Spesa"].nunique()
    n_pg_out = len(df_out)
    desc_parts = []
    if search_cap_text:
        desc_parts.append(f'capitolo: "{search_cap_text}"')
    if search_pg_text:
        desc_parts.append(f'PG: "{search_pg_text}"')
    if filtri_attivi:
        desc_parts.append(f"{len(filtri_attivi)} filtri attivi")

    st.caption(
        f"**{n_cap_out:,}** capitoli e **{n_pg_out:,}** PG trovati"
        + (f" ({', '.join(desc_parts)})" if desc_parts else "")
    )

    # --- Filtro Amministrazione sui risultati ---
    amm_risultati = sorted(df_out["Amministrazione"].unique())
    if len(amm_risultati) > 1:
        sel_amm_risultati = st.multiselect(
            "Filtra risultati per Amministrazione:",
            options=amm_risultati,
            default=amm_risultati,
            key="filtro_amm_risultati",
        )
        if sel_amm_risultati:
            df_out = df_out[df_out["Amministrazione"].isin(sel_amm_risultati)].copy()
        if df_out.empty:
            st.warning("Nessun risultato per le amministrazioni selezionate.")
            st.stop()

    caps_selezionati = visualizza_capitoli(df_out, mostra_selezione=True)
    sezione_export_e_assegnazione(df_out, caps_selezionati=caps_selezionati)

    # --- Rimuovi capitoli dalla mappatura ---
    user_ruolo = st.session_state.ruolo
    user_puo_mappare = is_super_admin() or user_ruolo in ["DIR.", "FUN."]

    if user_puo_mappare:
        st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
        st.markdown(
            '<div class="mef-page-title" style="font-size:17px">'
            'Rimuovi capitoli dalla mappatura</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            "Rimuove i capitoli trovati sopra dalla mappatura dell'ufficio selezionato."
        )

        col_rm1, col_rm2 = st.columns([1, 2])

        with col_rm1:
            if is_super_admin():
                uff_rimuovi = st.selectbox(
                    "Rimuovi da ufficio:",
                    options=["-- Seleziona --"] + [f"Ufficio {u}" for u in UFFICI],
                    key="uff_rimuovi",
                )
            else:
                proprio_ufficio = st.session_state.ufficio
                uff_rimuovi = f"Ufficio {proprio_ufficio}"
                st.info(f"Rimozione da: **{uff_rimuovi}**")

        with col_rm2:
            st.markdown("")
            st.markdown("")
            if uff_rimuovi != "-- Seleziona --":
                uff_rm_key = uff_rimuovi.replace("Ufficio ", "")
                mappatura = load_mappatura()
                esistenti = mappatura.get(uff_rm_key, [])

                caps_da_rimuovere = set(df_out["Numero Capitolo di Spesa"].unique())
                presenti = [r for r in esistenti if r["cap"] in caps_da_rimuovere]

                if not presenti:
                    st.caption(
                        f"Nessuno dei capitoli cercati e presente nella mappatura di {uff_rimuovi}."
                    )
                else:
                    caps_presenti = len(set(r["cap"] for r in presenti))
                    st.warning(
                        f"Trovati **{caps_presenti}** capitoli ({len(presenti)} PG) "
                        f"di {uff_rimuovi} corrispondenti alla ricerca."
                    )

                    if st.button(
                        f"Rimuovi {caps_presenti} capitoli / {len(presenti)} PG da {uff_rimuovi}",
                        key="btn_rimuovi",
                    ):
                        dopo = [r for r in esistenti if r["cap"] not in caps_da_rimuovere]
                        mappatura[uff_rm_key] = dopo
                        save_mappatura(mappatura)
                        st.success(
                            f"Rimossi **{len(presenti)}** PG da {uff_rimuovi}. "
                            f"Restano **{len(dopo)}** PG."
                        )
                        st.rerun()

    # --- SIDEBAR aggiuntiva ---
    with st.sidebar:
        st.markdown("---")
        st.header("Dataset")
        st.metric("Anno selezionato", str(anno_sel))
        st.metric("Amministrazioni", f"{df_anno['Amministrazione'].nunique()}")
        st.metric("Capitoli", f"{df_anno['Numero Capitolo di Spesa'].nunique():,}")

        if filtri_attivi:
            st.markdown("---")
            st.subheader("Filtri attivi")
            for nome, valori in filtri_attivi:
                for v in valori:
                    st.caption(f"{nome}: {v}")

        if search_cap_text or search_pg_text:
            st.markdown("---")
            st.subheader("Ricerca")
            if search_cap_text:
                st.caption(f'Capitolo: "{search_cap_text}"')
            if search_pg_text:
                st.caption(f'PG: "{search_pg_text}"')
            st.caption(f"{n_cap_out:,} capitoli, {n_pg_out:,} PG")


# ==================================================================
#         PAGINA 3 -- CONFRONTO ANNUALE
# ==================================================================

elif pagina == "Confronto Annuale":

    st.markdown("""
    <div class="mef-page-title">Confronto Annuale</div>
    <div class="mef-page-subtitle">
      Confronta due esercizi finanziari: individua PG scomparsi, nuovi e variazioni di stanziamento
    </div>
    """, unsafe_allow_html=True)

    # --- Selezione due anni ---
    col_a, col_b = st.columns(2)
    with col_a:
        anno_a = st.selectbox(
            "Anno di partenza (precedente):",
            options=sorted(anni_disponibili),
            index=max(0, len(anni_disponibili) - 2),
            key="confronto_anno_a",
        )
    with col_b:
        anno_b = st.selectbox(
            "Anno di arrivo (successivo):",
            options=sorted(anni_disponibili),
            index=len(anni_disponibili) - 1,
            key="confronto_anno_b",
        )

    if anno_a == anno_b:
        st.warning("Seleziona due anni diversi per il confronto.")
        st.stop()

    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)

    # --- Filtro Amministrazione ---
    st.markdown('<div class="mef-page-title" style="font-size:17px">Filtri</div>', unsafe_allow_html=True)

    # Unione delle amministrazioni presenti in entrambi gli anni
    df_a_full = df[df[ANNO_COL] == anno_a]
    df_b_full = df[df[ANNO_COL] == anno_b]
    amm_union = sorted(set(df_a_full["Amministrazione"].unique()) | set(df_b_full["Amministrazione"].unique()))

    sel_amm_conf = st.multiselect(
        "Amministrazioni (vuoto = tutte):",
        options=amm_union,
        key="conf_amm",
    )

    if sel_amm_conf:
        df_a = df_a_full[df_a_full["Amministrazione"].isin(sel_amm_conf)].copy()
        df_b = df_b_full[df_b_full["Amministrazione"].isin(sel_amm_conf)].copy()
    else:
        df_a = df_a_full.copy()
        df_b = df_b_full.copy()

    # Filtro opzionale per capitolo
    search_conf = st.text_input(
        "Filtra per numeri di capitolo (opzionale, separati da virgola):",
        placeholder="es. 7001, 7002",
        key="conf_cap_filter",
    )
    if search_conf:
        caps_filter = []
        for n in search_conf.split(","):
            n = n.strip()
            if n.isdigit():
                caps_filter.append(int(n))
        if caps_filter:
            df_a = df_a[df_a["Numero Capitolo di Spesa"].isin(caps_filter)].copy()
            df_b = df_b[df_b["Numero Capitolo di Spesa"].isin(caps_filter)].copy()

    if df_a.empty and df_b.empty:
        st.warning("Nessun dato trovato per i filtri selezionati.")
        st.stop()

    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)

    # --- Chiave univoca per PG ---
    KEY_COLS = ["Amministrazione", "Numero Capitolo di Spesa", "Numero Piano di Gestione"]

    def make_key(row):
        return (row["Amministrazione"], int(row["Numero Capitolo di Spesa"]), int(row["Numero Piano di Gestione"]))

    keys_a = set(df_a.apply(make_key, axis=1))
    keys_b = set(df_b.apply(make_key, axis=1))

    scomparsi_keys = keys_a - keys_b    # in A ma non in B
    nuovi_keys = keys_b - keys_a        # in B ma non in A
    comuni_keys = keys_a & keys_b       # in entrambi

    # --- TAB: Riepilogo / Scomparsi / Nuovi / Variazioni / Storico ---
    tab_riep, tab_scomp, tab_nuovi, tab_var, tab_storico = st.tabs([
        f"Riepilogo",
        f"Scomparsi ({len(scomparsi_keys)})",
        f"Nuovi ({len(nuovi_keys)})",
        f"Variazioni ({len(comuni_keys)})",
        "Storico pluriennale",
    ])

    # ---- TAB RIEPILOGO ----
    with tab_riep:
        st.markdown(f'<div class="mef-page-title" style="font-size:17px">Riepilogo {anno_a} vs {anno_b}</div>', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(f"PG in {anno_a}", f"{len(keys_a):,}")
        col2.metric(f"PG in {anno_b}", f"{len(keys_b):,}")
        col3.metric("PG scomparsi", f"{len(scomparsi_keys):,}")
        col4.metric("PG nuovi", f"{len(nuovi_keys):,}")

        # Totali CP
        tot_a = df_a["Legge di Bilancio CP A1"].sum()
        tot_b = df_b["Legge di Bilancio CP A1"].sum()
        delta = tot_b - tot_a
        pct = (delta / tot_a * 100) if tot_a != 0 else 0

        col5, col6, col7 = st.columns(3)
        col5.metric(f"Totale CP {anno_a}", fmt_eur(tot_a))
        col6.metric(f"Totale CP {anno_b}", fmt_eur(tot_b))
        col7.metric("Variazione", fmt_eur(delta), f"{pct:+.1f}%")

    # ---- TAB SCOMPARSI ----
    with tab_scomp:
        st.markdown(
            f'<div class="mef-page-title" style="font-size:17px">'
            f'PG presenti in {anno_a} ma assenti in {anno_b}</div>',
            unsafe_allow_html=True,
        )

        if not scomparsi_keys:
            st.success("Nessun PG scomparso!")
        else:
            rows_scomp = []
            for _, row in df_a.iterrows():
                k = make_key(row)
                if k in scomparsi_keys:
                    rows_scomp.append({
                        "Amministrazione": row["Amministrazione"],
                        "N. Capitolo": int(row["Numero Capitolo di Spesa"]),
                        "Capitolo": row["Capitolo di Spesa"],
                        "N. PG": int(row["Numero Piano di Gestione"]),
                        "Piano di Gestione": row["Piano di Gestione"],
                        f"CP {anno_a}": int(row["Legge di Bilancio CP A1"]),
                    })
            df_scomp = pd.DataFrame(rows_scomp).sort_values(["Amministrazione", "N. Capitolo", "N. PG"])

            tot_scomp = df_scomp[f"CP {anno_a}"].sum()
            st.metric("Stanziamento perso (PG scomparsi)", fmt_eur(tot_scomp))

            df_scomp_display = df_scomp.copy()
            df_scomp_display[f"CP {anno_a}"] = df_scomp_display[f"CP {anno_a}"].apply(fmt_eur)
            st.dataframe(df_scomp_display, use_container_width=True, hide_index=True)

            csv_scomp = df_scomp.to_csv(index=False, sep=";").encode("utf-8-sig")
            st.download_button(
                f"Scarica PG scomparsi ({len(df_scomp)} righe)",
                csv_scomp, f"pg_scomparsi_{anno_a}_vs_{anno_b}.csv", "text/csv",
                key="dl_scomp",
            )

    # ---- TAB NUOVI ----
    with tab_nuovi:
        st.markdown(
            f'<div class="mef-page-title" style="font-size:17px">'
            f'PG assenti in {anno_a} ma presenti in {anno_b}</div>',
            unsafe_allow_html=True,
        )

        if not nuovi_keys:
            st.success("Nessun PG nuovo!")
        else:
            rows_nuovi = []
            for _, row in df_b.iterrows():
                k = make_key(row)
                if k in nuovi_keys:
                    rows_nuovi.append({
                        "Amministrazione": row["Amministrazione"],
                        "N. Capitolo": int(row["Numero Capitolo di Spesa"]),
                        "Capitolo": row["Capitolo di Spesa"],
                        "N. PG": int(row["Numero Piano di Gestione"]),
                        "Piano di Gestione": row["Piano di Gestione"],
                        f"CP {anno_b}": int(row["Legge di Bilancio CP A1"]),
                    })
            df_nuovi = pd.DataFrame(rows_nuovi).sort_values(["Amministrazione", "N. Capitolo", "N. PG"])

            tot_nuovi = df_nuovi[f"CP {anno_b}"].sum()
            st.metric("Stanziamento nuovi PG", fmt_eur(tot_nuovi))

            df_nuovi_display = df_nuovi.copy()
            df_nuovi_display[f"CP {anno_b}"] = df_nuovi_display[f"CP {anno_b}"].apply(fmt_eur)
            st.dataframe(df_nuovi_display, use_container_width=True, hide_index=True)

            csv_nuovi = df_nuovi.to_csv(index=False, sep=";").encode("utf-8-sig")
            st.download_button(
                f"Scarica PG nuovi ({len(df_nuovi)} righe)",
                csv_nuovi, f"pg_nuovi_{anno_a}_vs_{anno_b}.csv", "text/csv",
                key="dl_nuovi",
            )

    # ---- TAB VARIAZIONI ----
    with tab_var:
        st.markdown(
            f'<div class="mef-page-title" style="font-size:17px">'
            f'Variazione stanziamento CP: {anno_a} vs {anno_b}</div>',
            unsafe_allow_html=True,
        )

        if not comuni_keys:
            st.info("Nessun PG in comune tra i due anni.")
        else:
            # Crea lookup per anno A e B
            lookup_a = {}
            for _, row in df_a.iterrows():
                k = make_key(row)
                if k in comuni_keys:
                    lookup_a[k] = row

            lookup_b = {}
            for _, row in df_b.iterrows():
                k = make_key(row)
                if k in comuni_keys:
                    lookup_b[k] = row

            rows_var = []
            for k in sorted(comuni_keys):
                ra = lookup_a[k]
                rb = lookup_b[k]
                cp_a = int(ra["Legge di Bilancio CP A1"])
                cp_b = int(rb["Legge di Bilancio CP A1"])
                delta_v = cp_b - cp_a
                pct_v = (delta_v / cp_a * 100) if cp_a != 0 else (100.0 if cp_b > 0 else 0.0)

                rows_var.append({
                    "Amministrazione": k[0],
                    "N. Capitolo": k[1],
                    "Capitolo": rb["Capitolo di Spesa"],
                    "N. PG": k[2],
                    "Piano di Gestione": rb["Piano di Gestione"],
                    f"CP {anno_a}": cp_a,
                    f"CP {anno_b}": cp_b,
                    "Variazione": delta_v,
                    "Var %": round(pct_v, 1),
                })

            df_var = pd.DataFrame(rows_var)

            # Filtro variazioni
            filtro_var = st.radio(
                "Mostra:",
                ["Tutti", "Solo aumenti", "Solo diminuzioni", "Solo invariati"],
                horizontal=True,
                key="filtro_var",
            )
            if filtro_var == "Solo aumenti":
                df_var = df_var[df_var["Variazione"] > 0]
            elif filtro_var == "Solo diminuzioni":
                df_var = df_var[df_var["Variazione"] < 0]
            elif filtro_var == "Solo invariati":
                df_var = df_var[df_var["Variazione"] == 0]

            # Ordinamento
            ord_var = st.selectbox(
                "Ordina per:",
                ["Variazione (decrescente)", "Variazione (crescente)",
                 "Var % (decrescente)", "Var % (crescente)",
                 "Capitolo"],
                key="ord_var",
            )
            if ord_var == "Variazione (decrescente)":
                df_var = df_var.sort_values("Variazione", ascending=False)
            elif ord_var == "Variazione (crescente)":
                df_var = df_var.sort_values("Variazione", ascending=True)
            elif ord_var == "Var % (decrescente)":
                df_var = df_var.sort_values("Var %", ascending=False)
            elif ord_var == "Var % (crescente)":
                df_var = df_var.sort_values("Var %", ascending=True)
            else:
                df_var = df_var.sort_values(["Amministrazione", "N. Capitolo", "N. PG"])

            # Metriche
            n_aum = (df_var["Variazione"] > 0).sum() if not df_var.empty else 0
            n_dim = (df_var["Variazione"] < 0).sum() if not df_var.empty else 0
            n_inv = (df_var["Variazione"] == 0).sum() if not df_var.empty else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PG mostrati", f"{len(df_var):,}")
            c2.metric("In aumento", f"{n_aum:,}")
            c3.metric("In diminuzione", f"{n_dim:,}")
            c4.metric("Invariati", f"{n_inv:,}")

            # Display
            df_var_display = df_var.copy()
            for col in [f"CP {anno_a}", f"CP {anno_b}", "Variazione"]:
                df_var_display[col] = df_var_display[col].apply(fmt_eur)
            df_var_display["Var %"] = df_var_display["Var %"].apply(lambda x: f"{x:+.1f}%")

            st.dataframe(df_var_display, use_container_width=True, hide_index=True)

            csv_var = df_var.to_csv(index=False, sep=";").encode("utf-8-sig")
            st.download_button(
                f"Scarica variazioni ({len(df_var)} righe)",
                csv_var, f"variazioni_{anno_a}_vs_{anno_b}.csv", "text/csv",
                key="dl_var",
            )

    # ---- TAB STORICO PLURIENNALE ----
    with tab_storico:
        st.markdown(
            '<div class="mef-page-title" style="font-size:17px">'
            'Storico stanziamento CP per capitolo/PG</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="mef-page-subtitle">'
            'Seleziona un capitolo per vedere come e variato lo stanziamento anno per anno</div>',
            unsafe_allow_html=True,
        )

        # Selezione amministrazione per restringere
        amm_storico = sorted(set(df_a_full["Amministrazione"].unique()) | set(df_b_full["Amministrazione"].unique()))
        if sel_amm_conf:
            amm_storico = sel_amm_conf

        sel_amm_storico = st.selectbox(
            "Amministrazione:",
            options=amm_storico,
            key="storico_amm",
        )

        df_amm_tutti = df[df["Amministrazione"] == sel_amm_storico]
        caps_storico = sorted(df_amm_tutti["Numero Capitolo di Spesa"].unique())

        sel_cap_storico = st.selectbox(
            "Capitolo di spesa:",
            options=caps_storico,
            format_func=lambda c: f"Cap. {c} -- {df_amm_tutti[df_amm_tutti['Numero Capitolo di Spesa'] == c]['Capitolo di Spesa'].iloc[0]}"
                if len(df_amm_tutti[df_amm_tutti['Numero Capitolo di Spesa'] == c]) > 0 else f"Cap. {c}",
            key="storico_cap",
        )

        df_cap_storico = df_amm_tutti[df_amm_tutti["Numero Capitolo di Spesa"] == sel_cap_storico]

        if df_cap_storico.empty:
            st.warning("Nessun dato per questo capitolo.")
        else:
            # Costruisci la tabella: righe = PG, colonne = anni
            pg_list = sorted(df_cap_storico["Numero Piano di Gestione"].unique())
            anni_presenti = sorted(df_cap_storico[ANNO_COL].unique())

            # Nome PG (prendi il piu recente)
            pg_names = {}
            for pg in pg_list:
                df_pg = df_cap_storico[df_cap_storico["Numero Piano di Gestione"] == pg]
                pg_names[pg] = df_pg.sort_values(ANNO_COL, ascending=False)["Piano di Gestione"].iloc[0]

            storico_rows = []
            for pg in pg_list:
                row = {
                    "N. PG": int(pg),
                    "Piano di Gestione": pg_names[pg],
                }
                for anno in anni_presenti:
                    df_pg_anno = df_cap_storico[
                        (df_cap_storico["Numero Piano di Gestione"] == pg)
                        & (df_cap_storico[ANNO_COL] == anno)
                    ]
                    if len(df_pg_anno) > 0:
                        row[f"CP {anno}"] = int(df_pg_anno["Legge di Bilancio CP A1"].sum())
                    else:
                        row[f"CP {anno}"] = None
                storico_rows.append(row)

            df_storico = pd.DataFrame(storico_rows)

            # Aggiungi riga totale
            totale_row = {"N. PG": "", "Piano di Gestione": "TOTALE CAPITOLO"}
            for anno in anni_presenti:
                col_name = f"CP {anno}"
                vals = df_storico[col_name].dropna()
                totale_row[col_name] = int(vals.sum()) if len(vals) > 0 else None
            df_storico = pd.concat([df_storico, pd.DataFrame([totale_row])], ignore_index=True)

            # Formattazione per display
            df_storico_display = df_storico.copy()
            for anno in anni_presenti:
                col_name = f"CP {anno}"
                df_storico_display[col_name] = df_storico_display[col_name].apply(
                    lambda x: fmt_eur(x) if pd.notna(x) else "—"
                )

            st.dataframe(df_storico_display, use_container_width=True, hide_index=True)

            # Variazioni anno su anno per il totale capitolo
            st.markdown(
                '<div class="mef-page-title" style="font-size:15px;margin-top:1rem">'
                'Variazione anno su anno (totale capitolo)</div>',
                unsafe_allow_html=True,
            )
            if len(anni_presenti) >= 2:
                var_rows = []
                for i in range(1, len(anni_presenti)):
                    a_prev = anni_presenti[i - 1]
                    a_curr = anni_presenti[i]
                    v_prev = totale_row.get(f"CP {a_prev}")
                    v_curr = totale_row.get(f"CP {a_curr}")
                    if v_prev is not None and v_curr is not None:
                        delta_s = v_curr - v_prev
                        pct_s = (delta_s / v_prev * 100) if v_prev != 0 else (100.0 if v_curr > 0 else 0.0)
                    else:
                        delta_s = None
                        pct_s = None
                    var_rows.append({
                        "Periodo": f"{a_prev} → {a_curr}",
                        f"CP {a_prev}": fmt_eur(v_prev) if v_prev is not None else "—",
                        f"CP {a_curr}": fmt_eur(v_curr) if v_curr is not None else "—",
                        "Variazione": fmt_eur(delta_s) if delta_s is not None else "—",
                        "Var %": f"{pct_s:+.1f}%" if pct_s is not None else "n/a",
                    })
                df_var_storico = pd.DataFrame(var_rows)
                st.dataframe(df_var_storico, use_container_width=True, hide_index=True)

            # Export
            csv_storico = df_storico.to_csv(index=False, sep=";").encode("utf-8-sig")
            st.download_button(
                f"Scarica storico Cap. {sel_cap_storico}",
                csv_storico,
                f"storico_cap_{sel_cap_storico}.csv",
                "text/csv",
                key="dl_storico",
            )

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("---")
        st.header("Confronto")
        st.caption(f"{anno_a} vs {anno_b}")
        st.metric("PG scomparsi", f"{len(scomparsi_keys):,}")
        st.metric("PG nuovi", f"{len(nuovi_keys):,}")
        st.metric("PG in comune", f"{len(comuni_keys):,}")


# ==================================================================
#         PAGINA 4 -- MAPPATURA UFFICI
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
            "Vai alla pagina di ricerca per assegnare "
            "capitoli e PG ai singoli uffici."
        )
        st.stop()

    if is_super_admin():
        uffici_visibili = UFFICI
    else:
        uffici_visibili = [st.session_state.ufficio]

    # --- Riepilogo ---
    st.markdown('<div class="mef-page-title" style="font-size:17px">Riepilogo</div>', unsafe_allow_html=True)

    summary_rows = []
    for uff in uffici_visibili:
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
    col_s1.metric("Uffici compilati", f"{compilati} / {len(uffici_visibili)}")
    col_s2.metric(
        "Totale PG mappati",
        f"{sum(r['Piani Gestionali'] for r in summary_rows):,}",
    )

    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # --- Dettaglio ---
    st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
    st.markdown('<div class="mef-page-title" style="font-size:17px">Dettaglio per Ufficio</div>', unsafe_allow_html=True)

    uffici_con_dati = [f"Ufficio {u}" for u in uffici_visibili if mappatura.get(u)]
    if not uffici_con_dati:
        st.info("Nessun ufficio ha ancora completato la mappatura.")
        st.stop()

    if is_super_admin() and len(uffici_visibili) > 1:
        vista = st.radio(
            "Visualizza:",
            options=["Singolo ufficio", "Tutti gli uffici"],
            horizontal=True,
            key="vista_mappa",
        )
        uffici_da_mostrare = uffici_visibili
        if vista == "Singolo ufficio":
            sel_uff_det = st.selectbox(
                "Seleziona ufficio:", options=uffici_con_dati, key="det_uff"
            )
            uffici_da_mostrare = [sel_uff_det.replace("Ufficio ", "")]
    else:
        uffici_da_mostrare = uffici_visibili
        vista = "Singolo ufficio"

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
            df_show = df_show.sort_values(["N. Capitolo", "N. PG"]).reset_index(drop=True)

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

    # --- Matrice (solo super admin) ---
    if is_super_admin():
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

    # --- Export completo (solo super admin) ---
    if is_super_admin():
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

    # --- Reset mappatura ---
    user_ruolo = st.session_state.ruolo
    user_puo_mappare = is_super_admin() or user_ruolo in ["DIR.", "FUN."]

    if user_puo_mappare:
        st.markdown('<hr class="mef-rule">', unsafe_allow_html=True)
        st.markdown('<div class="mef-page-title" style="font-size:17px">Resetta mappatura ufficio</div>', unsafe_allow_html=True)

        col_r1, col_r2 = st.columns([1, 2])
        with col_r1:
            if is_super_admin():
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

    # --- SIDEBAR Mappatura ---
    with st.sidebar:
        st.markdown("---")
        st.header("Stato compilazione")
        for uff in uffici_visibili:
            items = mappatura.get(uff, [])
            if items:
                caps = len(set(r["cap"] for r in items))
                st.caption(f"Uff. {uff}: {caps} cap., {len(items)} PG")
            else:
                st.caption(f"Uff. {uff}: da compilare")


# ===================================================================
#  FOOTER
# ===================================================================

st.markdown(
    f'<div class="mef-footer">'
    f"  <span>Ministero dell'Economia e delle Finanze -- Ragioneria Generale dello Stato</span>"
    f'  <span>Avviato: {start_time_str} &nbsp;|&nbsp; Legge di Bilancio {anni_disponibili[0]}-{anno_max}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

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
        f"Fonte: RGS -- Legge di Bilancio {anni_disponibili[0]}-{anno_max}"
        f"</div>",
        unsafe_allow_html=True,
    )
