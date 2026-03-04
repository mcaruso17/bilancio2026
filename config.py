import os

# Percorso del database SQLite
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "ispettorato.db")

# Lunghezza password generate automaticamente
PASSWORD_LENGTH = 12

# Ruoli riconosciuti dal sistema
RUOLI = ["DIR.", "FUN.", "ASS."]

# Uffici riconosciuti dal sistema
UFFICI = [str(i) for i in range(1, 14)] + ["CSR I", "CSR II"]

# Dominio email
EMAIL_DOMAIN = "mef.gov.it"

# Credenziali admin per il primo caricamento
ADMIN_USERNAME = "slimshady"
ADMIN_PASSWORD = "thislookslikeajobforme"
