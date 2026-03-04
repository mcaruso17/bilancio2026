import streamlit as st

# Lista degli utenti con accesso completo
SUPER_ADMIN_EMAILS = [
    "matteo.caruso@mef.gov.it",
    "giuseppe.olivieri@mef.gov.it",
    "alessandro.caianiello@mef.gov.it",
]

def get_user_ufficio():
    """Restituisce l'ufficio dell'utente corrente"""
    return st.session_state.get("ufficio", None)

def get_user_ruolo():
    """Restituisce il ruolo dell'utente corrente"""
    return st.session_state.get("ruolo", None)

def is_super_admin() -> bool:
    """Controlla se l'utente ha accesso completo a tutto"""
    return st.session_state.get("email", "") in SUPER_ADMIN_EMAILS

def is_admin() -> bool:
    """Controlla se l'utente è un dirigente"""
    return get_user_ruolo() == "DIR."

def puo_modificare(ufficio_dato: str) -> bool:
    """Controlla se l'utente può modificare (mappare/resettare) dati di quell'ufficio"""
    if is_super_admin():
        return True
    ruolo = get_user_ruolo()
    if ruolo in ["DIR.", "FUN."]:
        return get_user_ufficio() == ufficio_dato
    return False  # ASS. non può modificare

def puo_visualizzare(ufficio_dato: str) -> bool:
    """Controlla se l'utente può visualizzare dati di quell'ufficio"""
    if is_super_admin():
        return True
    return get_user_ufficio() == ufficio_dato

def richiedi_permesso(ufficio_dato: str, azione: str = "modificare"):
    """Mostra errore se l'utente non ha i permessi"""
    if azione == "modificare" and not puo_modificare(ufficio_dato):
        st.error("Non hai i permessi per modificare dati di questo ufficio")
        return False
    if azione == "visualizzare" and not puo_visualizzare(ufficio_dato):
        st.error("Non hai i permessi per visualizzare questi dati")
        return False
    return True
