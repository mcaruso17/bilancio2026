import hashlib
import secrets
import streamlit as st
from database import get_connection

class Authenticator:
    def __init__(self):
        """Inizializza la sessione se non esiste"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
            st.session_state.user_id = None
            st.session_state.nominativo = None
            st.session_state.email = None
            st.session_state.ruolo = None
            st.session_state.ufficio = None
            st.session_state.deve_cambiare_password = False
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """Genera hash della password con salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        pw_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return pw_hash.hex(), salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verifica se la password corrisponde"""
        pw_hash, _ = Authenticator.hash_password(password, salt)
        return pw_hash == stored_hash
    def login(self, email: str, password: str) -> tuple:
        """Verifica credenziali e avvia la sessione"""
        with get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ? AND attivo = 1",
                (email.lower().strip(),)
            ).fetchone()

        if user is None:
            return False, "Email o password non corretti"

        # Separa hash e salt (salvati come "hash:salt")
        stored_hash, salt = user["password_hash"].split(":")

        if not self.verify_password(password, stored_hash, salt):
            return False, "Email o password non corretti"

        # Login riuscito: salva i dati nella sessione
        st.session_state.authenticated = True
        st.session_state.user_id = user["id"]
        st.session_state.nominativo = user["nominativo"]
        st.session_state.email = user["email"]
        st.session_state.ruolo = user["ruolo"]
        st.session_state.ufficio = user["ufficio"]
        st.session_state.deve_cambiare_password = bool(user["deve_cambiare_password"])

        return True, "Login effettuato"

    def cambia_password(self, password_attuale: str, nuova_password: str) -> tuple:
        """Permette all'utente di cambiare la propria password"""
        if len(nuova_password) < 8:
            return False, "La password deve essere di almeno 8 caratteri"

        with get_connection() as conn:
            user = conn.execute(
                "SELECT password_hash FROM users WHERE id = ?",
                (st.session_state.user_id,)
            ).fetchone()

            stored_hash, salt = user["password_hash"].split(":")

            if not self.verify_password(password_attuale, stored_hash, salt):
                return False, "Password attuale non corretta"

            # Genera nuovo hash con nuovo salt
            new_hash, new_salt = self.hash_password(nuova_password)
            stored = f"{new_hash}:{new_salt}"

            conn.execute(
                "UPDATE users SET password_hash = ?, deve_cambiare_password = 0 WHERE id = ?",
                (stored, st.session_state.user_id)
            )

        st.session_state.deve_cambiare_password = False
        return True, "Password cambiata con successo"
    @staticmethod
    def reset_password(user_id: int) -> tuple:
        """Admin resetta la password di un utente"""
        nuova_password = secrets.token_urlsafe(12)
        new_hash, new_salt = Authenticator.hash_password(nuova_password)
        stored = f"{new_hash}:{new_salt}"

        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, deve_cambiare_password = 1 WHERE id = ?",
                (stored, user_id)
            )

        return nuova_password
    

@staticmethod
def logout():
    """Chiude la sessione"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
