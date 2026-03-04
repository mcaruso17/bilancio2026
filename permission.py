import streamlit as st

def get_user_ufficio():
    """Restituisce l'ufficio dell'utente corrente"""
    return st.session_state.get("ufficio", None)

def get_user_ruolo():
    """Restituisce il ruolo dell'utente corrente"""
    return st.session_state.get("ruolo", None)

def puo_modificare(ufficio_dato: str) -> bool:
    """Controlla se l'utente può modificare dati di quell'ufficio"""
    ruolo = get_user_ruolo()
    if ruolo == "DIR.":
        return True  # il direttore modifica tutto
    return get_user_ufficio() == ufficio_dato

def puo_visualizzare(ufficio_dato: str) -> bool:
    """Controlla se l'utente può visualizzare dati di quell'ufficio"""
    # Per ora tutti possono vedere tutto
    return True

def is_admin() -> bool:
    """Controlla se l'utente è un amministratore"""
    return get_user_ruolo() == "DIR."

def richiedi_permesso(ufficio_dato: str, azione: str = "modificare"):
    """Mostra errore se l'utente non ha i permessi"""
    if azione == "modificare" and not puo_modificare(ufficio_dato):
        st.error("Non hai i permessi per modificare dati di questo ufficio")
        return False
    if azione == "visualizzare" and not puo_visualizzare(ufficio_dato):
        st.error("Non hai i permessi per visualizzare questi dati")
        return False
    return True
