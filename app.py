import streamlit as st
import pandas as pd
import os
from datetime import datetime

start_time = datetime.now()
start_time_str = start_time.strftime("%d/%m/%Y %H:%M:%S")

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    IMPOSTAZIONI DA MODIFICARE                       ║
# ╚══════════════════════════════════════════════════════════════════════╝

BILANCIO_CSV = "bilancio2026.csv"

# ╔══════════════════════════════════════════════════════════════════════╗
# ║          FINE IMPOSTAZIONI - DA QUI IN GIÙ NON TOCCARE             ║
# ╚══════════════════════════════════════════════════════════════════════╝

st.set_page_config(
    page_title="Navigatore Legge di Bilancio 2026",
    page_icon="🏛️",
    layout="wide",
)

# ═══════════════════════════════════════════════════════════════════════
#  CARICAMENTO DATI
# ═══════════════════════════════════════════════════════════════════════

@st.cache_data
def load_bilancio():
    """Carica il dataset della Legge di Bilancio dal CSV."""
    if not os.path.exists(BILANCIO_CSV):
        return pd.DataFrame()
    df = pd.read_csv(BILANCIO_CSV, sep=";", encoding="utf-8-sig", low_memory=False)
    # Pulizia stringhe
    str_cols = df.select_dtypes(include="object").columns
    for c in str_cols:
        df[c] = df[c].astype(str).str.strip()
    # Converti importi in numerico
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


df = load_bilancio()
data_ok = not df.empty

# ═══════════════════════════════════════════════════════════════════════
#  INTESTAZIONE
# ═══════════════════════════════════════════════════════════════════════

st.title("🏛️ Navigatore Legge di Bilancio 2026")
st.markdown(
    "Naviga la struttura del bilancio dello Stato: "
    "**Amministrazione → Missione → Programma → Azione → "
    "Capitoli di Spesa e Piani Gestionali**.  \n"
    "È possibile selezionare **più voci** a ogni livello."
)

if not data_ok:
    st.error(
        f"❌ File `{BILANCIO_CSV}` non trovato. "
        "Assicurati che sia nella stessa cartella dell'app."
    )
    st.stop()

st.success(
    f"✅ Dataset caricato: **{len(df):,}** record — "
    f"**{df['Numero Capitolo di Spesa'].nunique():,}** capitoli di spesa"
)
st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════════════════════════

def fmt_eur(val):
    """Formatta un intero come importo EUR italiano."""
    if pd.isna(val) or val == 0:
        return "€ 0"
    return f"€ {int(val):,.0f}".replace(",", ".")


def build_label_map(df_slice, code_col, name_col):
    """
    Restituisce una lista ordinata di label 'CODICE — NOME'
    e un dict label→codice per il reverse lookup.
    """
    pairs = (
        df_slice[[code_col, name_col]]
        .drop_duplicates()
        .sort_values(code_col)
    )
    labels = [
        f"{row[code_col]:02d} — {row[name_col]}"
        for _, row in pairs.iterrows()
    ]
    label_to_code = {
        f"{row[code_col]:02d} — {row[name_col]}": row[code_col]
        for _, row in pairs.iterrows()
    }
    return labels, label_to_code


# ═══════════════════════════════════════════════════════════════════════
#  STEP 1 — AMMINISTRAZIONI
# ═══════════════════════════════════════════════════════════════════════

st.subheader("1️⃣ Amministrazioni")

amministrazioni = sorted(df["Amministrazione"].unique())
sel_amm = st.multiselect(
    "Seleziona una o più Amministrazioni:",
    options=amministrazioni,
    default=None,
    key="sel_amm",
)

if not sel_amm:
    st.info("👆 Seleziona almeno un'amministrazione per iniziare la navigazione.")
    st.stop()

df_filtered = df[df["Amministrazione"].isin(sel_amm)].copy()

# ═══════════════════════════════════════════════════════════════════════
#  STEP 2 — MISSIONI
# ═══════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("2️⃣ Missioni")

miss_labels, miss_map = build_label_map(df_filtered, "Codice Missione", "Missione")

sel_miss_labels = st.multiselect(
    "Seleziona una o più Missioni:",
    options=miss_labels,
    default=None,
    key="sel_miss",
)

if not sel_miss_labels:
    st.info("👆 Seleziona almeno una missione per proseguire.")
    st.stop()

sel_miss_codes = [miss_map[l] for l in sel_miss_labels]
df_filtered = df_filtered[df_filtered["Codice Missione"].isin(sel_miss_codes)].copy()

# ═══════════════════════════════════════════════════════════════════════
#  STEP 3 — PROGRAMMI
# ═══════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("3️⃣ Programmi")

prog_labels, prog_map = build_label_map(df_filtered, "Codice Programma", "Programma")

sel_prog_labels = st.multiselect(
    "Seleziona uno o più Programmi:",
    options=prog_labels,
    default=None,
    key="sel_prog",
)

if not sel_prog_labels:
    st.info("👆 Seleziona almeno un programma per proseguire.")
    st.stop()

sel_prog_codes = [prog_map[l] for l in sel_prog_labels]
df_filtered = df_filtered[df_filtered["Codice Programma"].isin(sel_prog_codes)].copy()

# ═══════════════════════════════════════════════════════════════════════
#  STEP 4 — AZIONI (opzionale)
# ═══════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("4️⃣ Azioni *(opzionale)*")

az_labels, az_map = build_label_map(df_filtered, "Codice Azione", "Azione")

sel_az_labels = st.multiselect(
    "Filtra per Azioni (lascia vuoto per includerle tutte):",
    options=az_labels,
    default=None,
    key="sel_azione",
)

if sel_az_labels:
    sel_az_codes = [az_map[l] for l in sel_az_labels]
    df_filtered = df_filtered[df_filtered["Codice Azione"].isin(sel_az_codes)].copy()

# ═══════════════════════════════════════════════════════════════════════
#  STEP 5 — TITOLO (opzionale)
# ═══════════════════════════════════════════════════════════════════════

titoli = sorted(df_filtered["Titolo"].unique())
if len(titoli) > 1:
    sel_titoli = st.multiselect(
        "Filtra per Titolo *(opzionale, lascia vuoto per tutti)*:",
        options=titoli,
        default=None,
        key="sel_titolo",
    )
    if sel_titoli:
        df_filtered = df_filtered[df_filtered["Titolo"].isin(sel_titoli)].copy()

# ═══════════════════════════════════════════════════════════════════════
#  OUTPUT — CAPITOLI DI SPESA E PIANI GESTIONALI
# ═══════════════════════════════════════════════════════════════════════

df_out = df_filtered.copy()

st.markdown("---")
st.subheader("📋 Capitoli di Spesa e Piani Gestionali")

n_cap_out = df_out["Numero Capitolo di Spesa"].nunique()
n_pg_out = len(df_out)
totale_cp_a1 = df_out["Legge di Bilancio CP A1"].sum()

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Capitoli di Spesa", f"{n_cap_out:,}")
col_m2.metric("Piani Gestionali", f"{n_pg_out:,}")
col_m3.metric("Totale CP 2026", fmt_eur(totale_cp_a1))

st.markdown("")

# --- Ricerca rapida nei risultati ---
search_q = st.text_input(
    "🔎 Cerca nei capitoli/piani gestionali:",
    placeholder="es. infrastrutture, ferroviario, 7001 …",
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
    n_cap_out = df_out["Numero Capitolo di Spesa"].nunique()
    st.caption(f"🔎 Filtro attivo: **{n_cap_out}** capitoli corrispondenti a \"{search_q}\"")

if df_out.empty:
    st.warning("Nessun risultato con i filtri selezionati.")
    st.stop()

# Raggruppa per Amministrazione → Capitolo
for amm in sorted(df_out["Amministrazione"].unique()):
    df_amm = df_out[df_out["Amministrazione"] == amm]
    st.markdown(f"### 🏢 {amm}")

    capitoli_unici = sorted(df_amm["Numero Capitolo di Spesa"].unique())

    for num_cap in capitoli_unici:
        df_cap = df_amm[df_amm["Numero Capitolo di Spesa"] == num_cap]
        nome_cap = df_cap["Capitolo di Spesa"].iloc[0]
        titolo_cap = df_cap["Titolo"].iloc[0]
        missione_cap = df_cap["Missione"].iloc[0]
        programma_cap = df_cap["Programma"].iloc[0]
        tot_cap = df_cap["Legge di Bilancio CP A1"].sum()

        with st.expander(
            f"📂 Cap. {num_cap} — {nome_cap}  |  {fmt_eur(tot_cap)}",
            expanded=False,
        ):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Titolo:** {titolo_cap}")
                st.markdown(f"**Missione:** {missione_cap}")
            with c2:
                st.markdown(f"**Programma:** {programma_cap}")
                st.markdown(
                    f"**Centro Responsabilità:** "
                    f"{', '.join(df_cap['Centro Responsabilità'].unique())}"
                )

            # Tabella piani gestionali
            display_cols = [
                "Numero Piano di Gestione",
                "Piano di Gestione",
                "Azione",
                "Legge di Bilancio CP A1",
                "Legge di Bilancio CP A2",
                "Legge di Bilancio CP A3",
                "Legge di Bilancio CS A1",
                "Legge di Bilancio RS A1",
            ]
            display_cols = [c for c in display_cols if c in df_cap.columns]
            df_display = df_cap[display_cols].copy()
            df_display = df_display.sort_values("Numero Piano di Gestione")

            rename_map = {
                "Numero Piano di Gestione": "N° PG",
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
                f"CP 2026 = {fmt_eur(df_cap['Legge di Bilancio CP A1'].sum())} · "
                f"CP 2027 = {fmt_eur(df_cap['Legge di Bilancio CP A2'].sum())} · "
                f"CP 2028 = {fmt_eur(df_cap['Legge di Bilancio CP A3'].sum())}"
            )


# ═══════════════════════════════════════════════════════════════════════
#  EXPORT CSV
# ═══════════════════════════════════════════════════════════════════════

st.markdown("---")
st.subheader("⬇️ Esporta selezione")

export_cols = [
    "Amministrazione",
    "Missione",
    "Programma",
    "Azione",
    "Titolo",
    "Numero Capitolo di Spesa",
    "Capitolo di Spesa",
    "Numero Piano di Gestione",
    "Piano di Gestione",
    "Centro Responsabilità",
    "Categoria",
    "Legge di Bilancio CP A1",
    "Legge di Bilancio CP A2",
    "Legge di Bilancio CP A3",
    "Legge di Bilancio CS A1",
    "Legge di Bilancio CS A2",
    "Legge di Bilancio CS A3",
    "Legge di Bilancio RS A1",
]
export_cols = [c for c in export_cols if c in df_out.columns]
df_export = df_out[export_cols].copy()

csv_data = df_export.to_csv(index=False, sep=";").encode("utf-8-sig")
st.download_button(
    label=f"⬇️ Scarica CSV ({len(df_export):,} righe)",
    data=csv_data,
    file_name="bilancio_2026_selezione.csv",
    mime="text/csv",
)

# ═══════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("📊 Statistiche Dataset")
    st.metric("Record totali", f"{len(df):,}")
    st.metric("Amministrazioni", f"{df['Amministrazione'].nunique()}")
    st.metric("Missioni", f"{df['Missione'].nunique()}")
    st.metric("Programmi", f"{df['Programma'].nunique()}")
    st.metric("Capitoli di Spesa", f"{df['Numero Capitolo di Spesa'].nunique():,}")

    st.markdown("---")

    st.subheader("🔍 Selezione corrente")
    if sel_amm:
        for a in sel_amm:
            st.markdown(f"- 🏢 {a}")
    if sel_miss_labels:
        for m in sel_miss_labels:
            st.markdown(f"- 🎯 {m}")
    if sel_prog_labels:
        for p in sel_prog_labels:
            st.markdown(f"- 📌 {p}")
    if sel_az_labels:
        for a in sel_az_labels:
            st.markdown(f"- ⚡ {a}")

    st.markdown("---")

    st.subheader("ℹ️ Navigazione")
    st.markdown(
        "```\n"
        "Amministrazione (multi)\n"
        "  └─ Missione (multi)\n"
        "       └─ Programma (multi)\n"
        "            └─ Azione (multi, opz.)\n"
        "                 └─ Capitolo di Spesa\n"
        "                      └─ Piano Gestionale\n"
        "```"
    )

    st.markdown("---")
    st.caption(f"Avviato: {start_time_str}")
    st.caption("Fonte: RGS — Legge di Bilancio 2026")
