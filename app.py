import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    IMPOSTAZIONI DA MODIFICARE                       ║
# ╚══════════════════════════════════════════════════════════════════════╝

BILANCIO_CSV = "bilancio2026.csv"
MAPPATURA_FILE = "mappatura_uffici.json"

UFFICI = [
    "I", "II", "III", "IV", "V", "VI", "VII",
    "VIII", "IX", "X", "XI", "XII", "XIII",
]

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


# ═══════════════════════════════════════════════════════════════════════
#  PERSISTENZA MAPPATURA (JSON)
# ═══════════════════════════════════════════════════════════════════════

def load_mappatura():
    """
    Carica la mappatura uffici dal file JSON.
    Struttura: { "I": [ {"cap": 7001, "pg": 1, ...}, ... ], ... }
    """
    if os.path.exists(MAPPATURA_FILE):
        try:
            with open(MAPPATURA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_mappatura(data):
    """Salva la mappatura uffici su file JSON."""
    with open(MAPPATURA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════
#  HELPER
# ═══════════════════════════════════════════════════════════════════════

def fmt_eur(val):
    if pd.isna(val) or val == 0:
        return "€ 0"
    return f"€ {int(val):,.0f}".replace(",", ".")


def build_label_map(df_slice, code_col, name_col):
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
#  CARICA DATI GLOBALI
# ═══════════════════════════════════════════════════════════════════════

df = load_bilancio()
data_ok = not df.empty

if not data_ok:
    st.error(
        f"❌ File `{BILANCIO_CSV}` non trovato. "
        "Assicurati che sia nella stessa cartella dell'app."
    )
    st.stop()

# ═══════════════════════════════════════════════════════════════════════
#  NAVIGAZIONE PAGINE
# ═══════════════════════════════════════════════════════════════════════

pagina = st.sidebar.radio(
    "📄 Pagina",
    options=["🔎 Navigatore e Selezione", "🗺️ Mappatura Uffici"],
    index=0,
)


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║             PAGINA 1 — NAVIGATORE E SELEZIONE                       ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════════╝

if pagina == "🔎 Navigatore e Selezione":

    st.title("🏛️ Navigatore Legge di Bilancio 2026")
    st.markdown(
        "Naviga il bilancio: **Amministrazione → Centro Responsabilità → "
        "Missione → Programma → Azione → Capitoli / PG**.  \n"
        "Seleziona **più voci** a ogni livello. "
        "Alla fine puoi **assegnare** i risultati a un ufficio."
    )
    st.success(
        f"✅ Dataset: **{len(df):,}** record — "
        f"**{df['Numero Capitolo di Spesa'].nunique():,}** capitoli"
    )
    st.markdown("---")

    # ─── STEP 1 — AMMINISTRAZIONI ─────────────────────────────────────
    st.subheader("1️⃣ Amministrazioni")
    amministrazioni = sorted(df["Amministrazione"].unique())
    sel_amm = st.multiselect(
        "Seleziona una o più Amministrazioni:",
        options=amministrazioni,
        key="sel_amm",
    )
    if not sel_amm:
        st.info("👆 Seleziona almeno un'amministrazione per iniziare.")
        st.stop()

    df_filtered = df[df["Amministrazione"].isin(sel_amm)].copy()

    # ─── STEP 2 — CENTRO RESPONSABILITÀ ───────────────────────────────
    st.markdown("---")
    st.subheader("2️⃣ Centro Responsabilità *(Dipartimento)*")

    cdr_options = sorted(df_filtered["Centro Responsabilità"].unique())
    sel_cdr = st.multiselect(
        "Seleziona uno o più Centri di Responsabilità (vuoto = tutti):",
        options=cdr_options,
        key="sel_cdr",
    )
    if sel_cdr:
        df_filtered = df_filtered[
            df_filtered["Centro Responsabilità"].isin(sel_cdr)
        ].copy()

    # ─── STEP 3 — MISSIONI ────────────────────────────────────────────
    st.markdown("---")
    st.subheader("3️⃣ Missioni")

    miss_labels, miss_map = build_label_map(
        df_filtered, "Codice Missione", "Missione"
    )
    sel_miss_labels = st.multiselect(
        "Seleziona una o più Missioni:",
        options=miss_labels,
        key="sel_miss",
    )
    if not sel_miss_labels:
        st.info("👆 Seleziona almeno una missione.")
        st.stop()

    sel_miss_codes = [miss_map[l] for l in sel_miss_labels]
    df_filtered = df_filtered[
        df_filtered["Codice Missione"].isin(sel_miss_codes)
    ].copy()

    # ─── STEP 4 — PROGRAMMI ───────────────────────────────────────────
    st.markdown("---")
    st.subheader("4️⃣ Programmi")

    prog_labels, prog_map = build_label_map(
        df_filtered, "Codice Programma", "Programma"
    )
    sel_prog_labels = st.multiselect(
        "Seleziona uno o più Programmi:",
        options=prog_labels,
        key="sel_prog",
    )
    if not sel_prog_labels:
        st.info("👆 Seleziona almeno un programma.")
        st.stop()

    sel_prog_codes = [prog_map[l] for l in sel_prog_labels]
    df_filtered = df_filtered[
        df_filtered["Codice Programma"].isin(sel_prog_codes)
    ].copy()

    # ─── STEP 5 — AZIONI (opzionale) ──────────────────────────────────
    st.markdown("---")
    st.subheader("5️⃣ Azioni *(opzionale)*")

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

    # ─── STEP 6 — TITOLO (opzionale) ──────────────────────────────────
    titoli = sorted(df_filtered["Titolo"].unique())
    if len(titoli) > 1:
        sel_titoli = st.multiselect(
            "Filtra per Titolo *(opzionale)*:",
            options=titoli,
            key="sel_titolo",
        )
        if sel_titoli:
            df_filtered = df_filtered[
                df_filtered["Titolo"].isin(sel_titoli)
            ].copy()

    # ═══════════════════════════════════════════════════════════════════
    #  OUTPUT — RISULTATI
    # ═══════════════════════════════════════════════════════════════════

    df_out = df_filtered.copy()

    st.markdown("---")
    st.subheader("📋 Capitoli di Spesa e Piani Gestionali")

    n_cap_out = df_out["Numero Capitolo di Spesa"].nunique()
    n_pg_out = len(df_out)
    totale_cp = df_out["Legge di Bilancio CP A1"].sum()

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Capitoli di Spesa", f"{n_cap_out:,}")
    col_m2.metric("Piani Gestionali", f"{n_pg_out:,}")
    col_m3.metric("Totale CP 2026", fmt_eur(totale_cp))

    # --- Ricerca rapida ---
    search_q = st.text_input(
        "🔎 Cerca nei risultati:",
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
        st.caption(
            f"🔎 **{df_out['Numero Capitolo di Spesa'].nunique()}** capitoli "
            f"corrispondenti a \"{search_q}\""
        )

    if df_out.empty:
        st.warning("Nessun risultato con i filtri selezionati.")
        st.stop()

    # --- Visualizzazione capitoli ---
    for amm in sorted(df_out["Amministrazione"].unique()):
        df_amm = df_out[df_out["Amministrazione"] == amm]
        st.markdown(f"### 🏢 {amm}")

        for num_cap in sorted(df_amm["Numero Capitolo di Spesa"].unique()):
            df_cap = df_amm[df_amm["Numero Capitolo di Spesa"] == num_cap]
            nome_cap = df_cap["Capitolo di Spesa"].iloc[0]
            tot_cap = df_cap["Legge di Bilancio CP A1"].sum()

            with st.expander(
                f"📂 Cap. {num_cap} — {nome_cap}  |  {fmt_eur(tot_cap)}",
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
                        f"{', '.join(df_cap['Centro Responsabilità'].unique())}"
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

    # ═══════════════════════════════════════════════════════════════════
    #  EXPORT CSV + ASSEGNAZIONE UFFICIO
    # ═══════════════════════════════════════════════════════════════════

    st.markdown("---")

    tab_csv, tab_ufficio = st.tabs(["⬇️ Esporta CSV", "🏷️ Assegna a Ufficio"])

    # --- Tab CSV ---
    with tab_csv:
        export_cols = [
            "Amministrazione", "Centro Responsabilità",
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
            label=f"⬇️ Scarica CSV ({len(df_out):,} righe)",
            data=csv_data,
            file_name="bilancio_2026_selezione.csv",
            mime="text/csv",
        )

    # --- Tab Assegna Ufficio ---
    with tab_ufficio:
        st.markdown(
            "Assegna **tutti** i capitoli e PG visualizzati sopra a un ufficio. "
            "Se l'ufficio ha già una mappatura, verrà **sovrascritta**."
        )

        col_uff, col_btn = st.columns([1, 2])

        with col_uff:
            ufficio_sel = st.selectbox(
                "Ufficio:",
                options=["— Seleziona —"] + [f"Ufficio {u}" for u in UFFICI],
                key="ufficio_assegna",
            )

        # Prepara record da salvare
        records = []
        for _, row in df_out.iterrows():
            records.append({
                "cap": int(row["Numero Capitolo di Spesa"]),
                "pg": int(row["Numero Piano di Gestione"]),
                "capitolo_spesa": row["Capitolo di Spesa"],
                "piano_gestione": row["Piano di Gestione"],
                "amministrazione": row["Amministrazione"],
                "centro_responsabilita": row["Centro Responsabilità"],
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
            if ufficio_sel != "— Seleziona —":
                ufficio_key = ufficio_sel.replace("Ufficio ", "")
                n_cap = df_out["Numero Capitolo di Spesa"].nunique()
                n_pg = len(df_out)

                if st.button(
                    f"✅ Assegna {n_cap} capitoli / {n_pg} PG → {ufficio_sel}",
                    type="primary",
                    key="btn_assegna",
                ):
                    mappatura = load_mappatura()
                    mappatura[ufficio_key] = records
                    save_mappatura(mappatura)
                    st.success(
                        f"✅ **{ufficio_sel}**: salvati **{n_cap}** capitoli e "
                        f"**{n_pg}** piani gestionali. "
                        f"(Mappatura precedente sovrascritta.)"
                    )
                    st.balloons()

        # Info su stato attuale ufficio
        if ufficio_sel != "— Seleziona —":
            ufficio_key = ufficio_sel.replace("Ufficio ", "")
            mappatura = load_mappatura()
            if ufficio_key in mappatura and mappatura[ufficio_key]:
                existing = mappatura[ufficio_key]
                caps_ex = len(set(r["cap"] for r in existing))
                st.info(
                    f"ℹ️ {ufficio_sel} ha attualmente **{caps_ex}** capitoli "
                    f"e **{len(existing)}** PG mappati. "
                    f"Premendo il pulsante verranno sostituiti."
                )

    # ═══════════════════════════════════════════════════════════════════
    #  SIDEBAR — Navigatore
    # ═══════════════════════════════════════════════════════════════════

    with st.sidebar:
        st.markdown("---")
        st.header("📊 Dataset")
        st.metric("Record totali", f"{len(df):,}")
        st.metric("Amministrazioni", f"{df['Amministrazione'].nunique()}")
        st.metric("Capitoli", f"{df['Numero Capitolo di Spesa'].nunique():,}")

        st.markdown("---")
        st.subheader("🔍 Filtri attivi")
        if sel_amm:
            for a in sel_amm:
                st.caption(f"🏢 {a}")
        if sel_cdr:
            for c in sel_cdr:
                st.caption(f"🏗️ {c}")
        if sel_miss_labels:
            for m in sel_miss_labels:
                st.caption(f"🎯 {m}")
        if sel_prog_labels:
            for p in sel_prog_labels:
                st.caption(f"📌 {p}")
        if sel_az_labels:
            for a in sel_az_labels:
                st.caption(f"⚡ {a}")

        st.markdown("---")
        st.caption(
            "```\n"
            "Amministrazione\n"
            "  └─ Centro Responsabilità\n"
            "       └─ Missione\n"
            "            └─ Programma\n"
            "                 └─ Azione\n"
            "                      └─ Capitolo\n"
            "                           └─ PG\n"
            "```"
        )


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║             PAGINA 2 — MAPPATURA UFFICI                              ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════════╝

elif pagina == "🗺️ Mappatura Uffici":

    st.title("🗺️ Mappatura Uffici — Capitoli e Piani Gestionali")
    st.markdown(
        "Visualizza quali **capitoli di spesa e piani gestionali** "
        "sono stati assegnati a ciascun ufficio dell'ispettorato."
    )

    mappatura = load_mappatura()

    if not mappatura:
        st.info(
            "📭 Nessuna mappatura salvata. "
            "Vai alla pagina **Navigatore e Selezione** per assegnare "
            "capitoli e PG ai singoli uffici."
        )
        st.stop()

    # ─── Riepilogo generale ───────────────────────────────────────────
    st.subheader("📊 Riepilogo")

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
                "Stato": "✅ Compilato",
            })
        else:
            summary_rows.append({
                "Ufficio": f"Ufficio {uff}",
                "Capitoli": 0,
                "Piani Gestionali": 0,
                "Totale CP 2026": "€ 0",
                "Stato": "⬜ Da compilare",
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

    # ─── Dettaglio per ufficio ────────────────────────────────────────
    st.markdown("---")
    st.subheader("📂 Dettaglio per Ufficio")

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
            f"🏷️ Ufficio {uff} — {caps} capitoli, {pg_count} PG, "
            f"CP 2026: {fmt_eur(tot_cp)}",
            expanded=(vista == "Singolo ufficio"),
        ):
            display_cols_map = {
                "cap": "N° Capitolo",
                "capitolo_spesa": "Capitolo di Spesa",
                "pg": "N° PG",
                "piano_gestione": "Piano di Gestione",
                "amministrazione": "Amministrazione",
                "centro_responsabilita": "Centro Responsabilità",
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
                ["N° Capitolo", "N° PG"]
            ).reset_index(drop=True)

            for col in ["CP 2026", "CP 2027", "CP 2028"]:
                if col in df_show.columns:
                    df_show[col] = df_show[col].apply(fmt_eur)

            st.dataframe(df_show, use_container_width=True, hide_index=True)

            csv_uff = df_show.to_csv(index=False, sep=";").encode("utf-8-sig")
            st.download_button(
                label=f"⬇️ Scarica CSV Ufficio {uff}",
                data=csv_uff,
                file_name=f"mappatura_ufficio_{uff}.csv",
                mime="text/csv",
                key=f"dl_uff_{uff}",
            )

    # ─── Matrice Cap × Ufficio ────────────────────────────────────────
    st.markdown("---")
    st.subheader("🔀 Matrice Capitoli × Uffici")
    st.markdown(
        "Quali uffici sono competenti su ciascun capitolo? "
        "Utile per individuare sovrapposizioni."
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
                row[f"Uff. {uff}"] = "✅" if cap in caps_uff else ""
            matrix_rows.append(row)

        df_matrix = pd.DataFrame(matrix_rows)
        st.dataframe(df_matrix, use_container_width=True, hide_index=True)

        csv_matrix = df_matrix.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="⬇️ Scarica matrice Cap × Uffici (CSV)",
            data=csv_matrix,
            file_name="matrice_capitoli_uffici.csv",
            mime="text/csv",
            key="dl_matrice",
        )
    else:
        st.info("Nessun capitolo mappato.")

    # ─── Export completo ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("⬇️ Export completo mappatura")

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
            label=f"⬇️ Scarica mappatura completa ({len(df_all):,} righe)",
            data=csv_all,
            file_name="mappatura_completa_uffici.csv",
            mime="text/csv",
            key="dl_all",
        )

    # ─── Reset singolo ufficio ────────────────────────────────────────
    st.markdown("---")
    st.subheader("🗑️ Resetta mappatura ufficio")

    col_r1, col_r2 = st.columns([1, 2])
    with col_r1:
        uff_reset = st.selectbox(
            "Ufficio da resettare:",
            options=["— Seleziona —"] + [f"Ufficio {u}" for u in UFFICI],
            key="uff_reset",
        )
    with col_r2:
        st.markdown("")
        st.markdown("")
        if uff_reset != "— Seleziona —":
            uff_key = uff_reset.replace("Ufficio ", "")
            if mappatura.get(uff_key):
                if st.button(
                    f"🗑️ Cancella mappatura {uff_reset}",
                    key="btn_reset",
                ):
                    mappatura[uff_key] = []
                    save_mappatura(mappatura)
                    st.success(f"🗑️ Mappatura di {uff_reset} cancellata.")
                    st.rerun()
            else:
                st.caption(f"{uff_reset} non ha mappature.")

    # ─── SIDEBAR — Mappatura ──────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.header("📊 Stato compilazione")
        for uff in UFFICI:
            items = mappatura.get(uff, [])
            if items:
                caps = len(set(r["cap"] for r in items))
                st.caption(f"✅ Uff. {uff}: {caps} cap., {len(items)} PG")
            else:
                st.caption(f"⬜ Uff. {uff}: da compilare")


# ═══════════════════════════════════════════════════════════════════════
#  FOOTER SIDEBAR (comune)
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("---")
    st.caption(f"Avviato: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    st.caption("Fonte: RGS — Legge di Bilancio 2026")
