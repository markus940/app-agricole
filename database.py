import sqlite3
import json
import os
import csv
from datetime import date

DB_FILE = "agriculture.db"
CSV_PRIX = "prix_marche.csv"


def get_connection():
    """Crée et retourne une connexion SQLite avec row_factory sous forme de dictionnaire."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialise les tables de la base de données SQLite si elles n'existent pas."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Table Exploitation (une ligne par utilisateur)
        cursor.execute("DROP TABLE IF EXISTS exploitation")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exploitation (
                user_id INTEGER PRIMARY KEY,
                nom TEXT,
                region TEXT,
                departement TEXT,
                commune TEXT,
                localite TEXT,
                superficie_totale REAL DEFAULT 0.0,
                type_sol TEXT,
                irrigation TEXT,
                cultures_principales TEXT
            )
        """)

        # Table Parcelles (avec coordonnées GPS)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parcelles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                superficie REAL NOT NULL,
                culture TEXT NOT NULL,
                localisation TEXT,
                campagne TEXT,
                statut TEXT DEFAULT '🟡 Planifiée',
                latitude REAL DEFAULT 14.79,
                longitude REAL DEFAULT -16.92
            )
        """)

        # Table Campagnes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campagnes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parcelle TEXT NOT NULL,
                culture TEXT NOT NULL,
                superficie REAL NOT NULL,
                date_semis TEXT NOT NULL,
                date_recolte_prevue TEXT,
                statut TEXT DEFAULT '🔵 En cours'
            )
        """)

        # Table Dépenses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campagne TEXT NOT NULL,
                culture TEXT NOT NULL,
                date TEXT NOT NULL,
                categorie TEXT NOT NULL,
                description TEXT NOT NULL,
                quantite REAL DEFAULT 0.0,
                prix_unitaire REAL DEFAULT 0.0,
                montant REAL NOT NULL
            )
        """)

        # Table Récoltes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recoltes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campagne TEXT NOT NULL,
                culture TEXT NOT NULL,
                date TEXT NOT NULL,
                superficie REAL DEFAULT 0.0,
                quantite_kg REAL NOT NULL,
                rendement_kg_ha REAL
            )
        """)

        # Table Ventes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campagne TEXT NOT NULL,
                culture TEXT NOT NULL,
                date TEXT NOT NULL,
                acheteur TEXT,
                quantite_kg REAL NOT NULL,
                prix_unitaire REAL NOT NULL,
                montant REAL NOT NULL
            )
        """)

        # Table Prix de marché communautaires
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prix_marche (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                culture TEXT NOT NULL,
                localite TEXT NOT NULL,
                prix_fcfa_kg REAL NOT NULL
            )
        """)

        # Table Stocks d'Intrants et Matériel
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                categorie TEXT NOT NULL,
                quantite REAL DEFAULT 0.0,
                unite TEXT DEFAULT 'kg',
                seuil_alerte REAL DEFAULT 5.0,
                emplacement TEXT
            )
        """)

        # Table Carnet d'Adresses (Acheteurs & Fournisseurs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                role TEXT NOT NULL,
                telephone TEXT,
                localite TEXT,
                produits TEXT,
                remarques TEXT
            )
        """)

        # Table Pluviométrie (Relevés des pluies en mm par parcelle)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pluviometrie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                parcelle TEXT NOT NULL,
                mm_pluie REAL NOT NULL,
                remarques TEXT
            )
        """)
# Table Utilisateurs (comptes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                date_creation TEXT NOT NULL
            )
        """)
        # Ajout de la colonne user_id sur les tables existantes (migration en douceur)
        for table in ["parcelles", "campagnes", "depenses", "recoltes", "ventes", "stocks", "contacts", "ouvriers", "jours_travail"]:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER")
            except sqlite3.OperationalError:
                pass  # la colonne existe déjà, rien à faire
            # Table Ouvriers (Main d'œuvre)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ouvriers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                nom TEXT NOT NULL,
                telephone TEXT,
                specialite TEXT,
                date_creation TEXT DEFAULT CURRENT_DATE
            )
        """)

        # Table Jours de travail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jours_travail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                ouvrier_id INTEGER NOT NULL,
                date_travail TEXT NOT NULL,
                nombre_jours REAL NOT NULL DEFAULT 1.0,
                salaire_journalier REAL NOT NULL DEFAULT 0.0,
                parcelle_id INTEGER,
                campagne_id INTEGER,
                remarque TEXT,
                FOREIGN KEY (ouvrier_id) REFERENCES ouvriers (id)
            )
        """)
        conn.commit()

    _migrer_csv_prix()


def _migrer_csv_prix():
    if os.path.exists(CSV_PRIX):
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM prix_marche")
            if cursor.fetchone()["count"] == 0:
                with open(CSV_PRIX, "r", encoding="utf-8", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            cursor.execute(
                                "INSERT INTO prix_marche (date, culture, localite, prix_fcfa_kg) VALUES (?, ?, ?, ?)",
                                (row["date"], row["culture"], row["localite"], float(row["prix_fcfa_kg"]))
                            )
                        except (KeyError, ValueError):
                            continue
                conn.commit()


# --- EXPLOITATION ---
def get_exploitation(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM exploitation WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["cultures_principales"] = json.loads(data["cultures_principales"]) if data["cultures_principales"] else []
            return data
        return {}


def save_exploitation(user_id, data):
    cultures_json = json.dumps(data.get("cultures_principales", []), ensure_ascii=False)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO exploitation (user_id, nom, region, departement, commune, localite, superficie_totale, type_sol, irrigation, cultures_principales)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                nom=excluded.nom,
                region=excluded.region,
                departement=excluded.departement,
                commune=excluded.commune,
                localite=excluded.localite,
                superficie_totale=excluded.superficie_totale,
                type_sol=excluded.type_sol,
                irrigation=excluded.irrigation,
                cultures_principales=excluded.cultures_principales
        """, (
            user_id,
            data.get("nom", ""),
            data.get("region", ""),
            data.get("departement", ""),
            data.get("commune", ""),
            data.get("localite", ""),
            float(data.get("superficie_totale", 0.0)),
            data.get("type_sol", ""),
            data.get("irrigation", ""),
            cultures_json
        ))
        conn.commit()


# --- PARCELLES ---
def get_parcelles(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parcelles WHERE user_id = ? ORDER BY id DESC", (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def add_parcelle(user_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO parcelles (nom, superficie, culture, localisation, campagne, statut, latitude, longitude, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["nom"], float(data["superficie"]), data["culture"],
            data.get("localisation", ""), data.get("campagne", ""), data.get("statut", "🟡 Planifiée"),
            float(data.get("latitude", 14.79)), float(data.get("longitude", -16.92)), user_id
        ))
        conn.commit()


def delete_parcelle(user_id, parcelle_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parcelles WHERE id = ? AND user_id = ?", (parcelle_id, user_id))
        conn.commit()


# --- CAMPAGNES ---
def get_campagnes(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM campagnes WHERE user_id = ? ORDER BY id DESC", (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def add_campagne(user_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO campagnes (parcelle, culture, superficie, date_semis, date_recolte_prevue, statut, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["parcelle"], data["culture"], float(data["superficie"]),
            str(data["date_semis"]), str(data["date_recolte_prevue"]) if data.get("date_recolte_prevue") else None,
            data.get("statut", "🔵 En cours"), user_id
        ))
        conn.commit()


def delete_campagne(user_id, campagne_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM campagnes WHERE id = ? AND user_id = ?", (campagne_id, user_id))
        conn.commit()


# --- DÉPENSES ---
def get_depenses(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM depenses WHERE user_id = ? ORDER BY date DESC, id DESC", (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def add_depense(user_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO depenses (campagne, culture, date, categorie, description, quantite, prix_unitaire, montant, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["campagne"], data["culture"], str(data["date"]),
            data["categorie"], data["description"], float(data.get("quantite", 0.0)),
            float(data.get("prix_unitaire", 0.0)), float(data["montant"]), user_id
        ))
        conn.commit()


def delete_depense(user_id, depense_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM depenses WHERE id = ? AND user_id = ?", (depense_id, user_id))
        conn.commit()


# --- RÉCOLTES ---
def get_recoltes(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recoltes WHERE user_id = ? ORDER BY date DESC, id DESC", (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def add_recolte(user_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recoltes (campagne, culture, date, superficie, quantite_kg, rendement_kg_ha, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["campagne"], data["culture"], str(data["date"]),
            float(data.get("superficie", 0.0)), float(data["quantite_kg"]),
            float(data["rendement_kg_ha"]) if data.get("rendement_kg_ha") is not None else None,
            user_id
        ))
        conn.commit()


def delete_recolte(user_id, recolte_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recoltes WHERE id = ? AND user_id = ?", (recolte_id, user_id))
        conn.commit()


# --- VENTES ---
def get_ventes(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ventes WHERE user_id = ? ORDER BY date DESC, id DESC", (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def add_vente(user_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ventes (campagne, culture, date, acheteur, quantite_kg, prix_unitaire, montant, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["campagne"], data["culture"], str(data["date"]),
            data.get("acheteur", ""), float(data["quantite_kg"]),
            float(data["prix_unitaire"]), float(data["montant"]), user_id
        ))
        conn.commit()


def delete_vente(user_id, vente_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ventes WHERE id = ? AND user_id = ?", (vente_id, user_id))
        conn.commit()


# --- PRIX DU MARCHÉ ---
def get_prix_marche(culture=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if culture:
            cursor.execute("SELECT * FROM prix_marche WHERE culture = ? ORDER BY date DESC, id DESC LIMIT 15", (culture,))
        else:
            cursor.execute("SELECT * FROM prix_marche ORDER BY date DESC, id DESC LIMIT 30")
        return [dict(r) for r in cursor.fetchall()]


def count_prix_marche():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM prix_marche")
        return cursor.fetchone()["count"]


def add_prix_marche(culture, localite, prix_fcfa_kg):
    today_str = date.today().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO prix_marche (date, culture, localite, prix_fcfa_kg)
            VALUES (?, ?, ?, ?)
        """, (today_str, culture, localite, float(prix_fcfa_kg)))
        conn.commit()


# --- STOCKS ---
def get_stocks(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM stocks WHERE user_id = ? ORDER BY categorie ASC, nom ASC", (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def add_stock(user_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO stocks (nom, categorie, quantite, unite, seuil_alerte, emplacement, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["nom"], data["categorie"], float(data.get("quantite", 0.0)),
            data.get("unite", "kg"), float(data.get("seuil_alerte", 5.0)),
            data.get("emplacement", "Magasin Principal"), user_id
        ))
        conn.commit()


def update_stock_quantite(user_id, stock_id, delta):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE stocks SET quantite = MAX(0, quantite + ?) WHERE id = ? AND user_id = ?",
            (float(delta), stock_id, user_id)
        )
        conn.commit()


def delete_stock(user_id, stock_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM stocks WHERE id = ? AND user_id = ?", (stock_id, user_id))
        conn.commit()


# --- CONTACTS (Carnet d'Adresses) ---
def get_contacts(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contacts WHERE user_id = ? ORDER BY role ASC, nom ASC", (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def add_contact(user_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contacts (nom, role, telephone, localite, produits, remarques, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["nom"], data["role"], data.get("telephone", ""),
            data.get("localite", ""), data.get("produits", ""), data.get("remarques", ""), user_id
        ))
        conn.commit()


def delete_contact(user_id, contact_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ? AND user_id = ?", (contact_id, user_id))
        conn.commit()


# --- PLUVIOMÉTRIE ---
def get_pluviometrie(parcelle=None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if parcelle:
            cursor.execute("SELECT * FROM pluviometrie WHERE parcelle = ? ORDER BY date DESC, id DESC", (parcelle,))
        else:
            cursor.execute("SELECT * FROM pluviometrie ORDER BY date DESC, id DESC")
        return [dict(r) for r in cursor.fetchall()]


def add_pluviometrie(data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pluviometrie (date, parcelle, mm_pluie, remarques)
            VALUES (?, ?, ?, ?)
        """, (
            str(data["date"]), data["parcelle"], float(data["mm_pluie"]), data.get("remarques", "")
        ))
        conn.commit()


def delete_pluviometrie(pluv_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pluviometrie WHERE id = ?", (pluv_id,))
        conn.commit()


# --- SAUVEGARDE & RESTAURATION ---
def export_db_bytes():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "rb") as f:
            return f.read()
    return b""


def import_db_bytes(file_bytes):
    with open(DB_FILE, "wb") as f:
        f.write(file_bytes)
# --- UTILISATEURS (comptes) ---
import hashlib
import secrets


def _hasher_mot_de_passe(mot_de_passe, salt):
    """Transforme un mot de passe en empreinte impossible à inverser, à l'aide d'un sel aléatoire."""
    return hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), salt.encode(), 100_000).hex()


def creer_utilisateur(username, mot_de_passe):
    """Crée un nouveau compte. Renvoie True si réussi, False si le nom existe déjà."""
    salt = secrets.token_hex(16)
    password_hash = _hasher_mot_de_passe(mot_de_passe, salt)
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, date_creation) VALUES (?, ?, ?, ?)",
                (username, password_hash, salt, date.today().isoformat()),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # le nom d'utilisateur existe déjà


def verifier_utilisateur(username, mot_de_passe):
    """Vérifie les identifiants. Renvoie l'id de l'utilisateur si correct, sinon None."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()

    if row is None:
        return None

    hash_calcule = _hasher_mot_de_passe(mot_de_passe, row["salt"])
    if hash_calcule == row["password_hash"]:
        return row["id"]
    return None


# ====================== MAIN D'ŒUVRE ======================

def get_ouvriers(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ouvriers WHERE user_id = ? ORDER BY nom ASC", (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def add_ouvrier(user_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ouvriers (user_id, nom, telephone, specialite)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            data["nom"],
            data.get("telephone", ""),
            data.get("specialite", "")
        ))
        conn.commit()


def delete_ouvrier(user_id, ouvrier_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        # On supprime aussi les jours de travail liés
        cursor.execute("DELETE FROM jours_travail WHERE ouvrier_id = ? AND user_id = ?", (ouvrier_id, user_id))
        cursor.execute("DELETE FROM ouvriers WHERE id = ? AND user_id = ?", (ouvrier_id, user_id))
        conn.commit()


def get_jours_travail(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT jt.*, o.nom as ouvrier_nom
            FROM jours_travail jt
            JOIN ouvriers o ON jt.ouvrier_id = o.id
            WHERE jt.user_id = ?
            ORDER BY jt.date_travail DESC
        """, (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def add_jour_travail(user_id, data):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jours_travail 
            (user_id, ouvrier_id, date_travail, nombre_jours, salaire_journalier, parcelle_id, campagne_id, remarque)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            data["ouvrier_id"],
            data["date_travail"],
            float(data.get("nombre_jours", 1.0)),
            float(data.get("salaire_journalier", 0.0)),
            data.get("parcelle_id"),
            data.get("campagne_id"),
            data.get("remarque", "")
        ))
        conn.commit()


def delete_jour_travail(user_id, jour_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jours_travail WHERE id = ? AND user_id = ?", (jour_id, user_id))
        conn.commit()