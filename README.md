# 🏛️ Navigatore Legge di Bilancio 2026

App Streamlit per navigare la struttura della Legge di Bilancio dello Stato italiano (esercizio 2026), dalla selezione dell'Amministrazione fino ai singoli Capitoli di Spesa e Piani Gestionali.

## Funzionalità

- **Selezione multipla** a ogni livello: Amministrazione, Missione, Programma, Azione
- **Navigazione gerarchica** a cascata: ogni filtro restringe le opzioni successive
- **Dettaglio completo** per ogni Capitolo di Spesa con i Piani Gestionali e gli importi CP/CS/RS triennio 2026–2028
- **Ricerca testuale** rapida nei risultati
- **Export CSV** della selezione corrente
- **Sidebar** con statistiche e riepilogo dei filtri attivi

## Struttura del repository

```
├── app.py                  # App Streamlit
├── bilancio2026.csv        # Dataset Legge di Bilancio 2026 (sep=;)
├── requirements.txt        # Dipendenze Python
├── .streamlit/
│   └── config.toml         # Configurazione tema
└── README.md
```

## Esecuzione locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy su Streamlit Community Cloud (gratuito)

1. Crea un repository GitHub e carica tutti i file (incluso `bilancio2026.csv`)
2. Vai su [share.streamlit.io](https://share.streamlit.io)
3. Clicca **New app** e collega il repository
4. Imposta `app.py` come Main file path
5. Clicca **Deploy**

L'app sarà disponibile con un URL pubblico permanente.

## Fonte dati

Ragioneria Generale dello Stato — Legge di Bilancio 2026, Spese, Piano di Gestione.
