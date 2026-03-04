import sqlite3
from contextlib import contextmanager
from config import DATABASE_PATH

@contextmanager
def get_connection():
    """Apre una connessione al DB e la chiude automaticamente"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # permette di accedere ai campi per nome
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Crea la tabella utenti se non esiste"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nominativo TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                ruolo TEXT NOT NULL,
                ufficio TEXT NOT NULL,
                stanza TEXT,
                interno TEXT,
                cellulare TEXT,
                deve_cambiare_password BOOLEAN DEFAULT 1,
                attivo BOOLEAN DEFAULT 1,
                data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
