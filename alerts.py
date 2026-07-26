"""
alerts.py
Gestión de alertas de usuarios: creación, listado, y evaluación contra precios actuales.
Persistencia simple con SQLite (un solo archivo, sin necesidad de instalar servidor de BD).
"""
import os
import sqlite3
from dataclasses import dataclass

# Si existe un volumen persistente montado (ej: en Railway en /data),
# la base de datos se guarda ahí para no perderse entre despliegues.
# En tu compu local, como no existe /data, usa simplemente "alerts.db".
_DATA_DIR = "/data" if os.path.isdir("/data") else "."
DB_PATH = os.path.join(_DATA_DIR, "alerts.db")


@dataclass
class Alert:
    id: int
    chat_id: int
    asset: str        # ej: "blue", "bitcoin", "oficial"
    operator: str      # "<" o ">"
    target_value: float
    active: bool


def init_db(db_path: str = DB_PATH) -> None:
    """Crea la tabla de alertas si no existe."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            asset TEXT NOT NULL,
            operator TEXT NOT NULL,
            target_value REAL NOT NULL,
            active INTEGER NOT NULL DEFAULT 1
        )
        """
    )
    conn.commit()
    conn.close()


def add_alert(chat_id: int, asset: str, operator: str, target_value: float, db_path: str = DB_PATH) -> int:
    """Guarda una nueva alerta y devuelve su id."""
    if operator not in ("<", ">"):
        raise ValueError("El operador debe ser '<' o '>'")

    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "INSERT INTO alerts (chat_id, asset, operator, target_value, active) VALUES (?, ?, ?, ?, 1)",
        (chat_id, asset.lower(), operator, target_value),
    )
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    return alert_id


def list_alerts(chat_id: int, only_active: bool = True, db_path: str = DB_PATH) -> list[Alert]:
    """Lista las alertas de un usuario."""
    conn = sqlite3.connect(db_path)
    query = "SELECT id, chat_id, asset, operator, target_value, active FROM alerts WHERE chat_id = ?"
    if only_active:
        query += " AND active = 1"
    rows = conn.execute(query, (chat_id,)).fetchall()
    conn.close()
    return [Alert(id=r[0], chat_id=r[1], asset=r[2], operator=r[3], target_value=r[4], active=bool(r[5])) for r in rows]


def get_all_active_alerts(db_path: str = DB_PATH) -> list[Alert]:
    """Lista todas las alertas activas de todos los usuarios (para el chequeo periódico)."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT id, chat_id, asset, operator, target_value, active FROM alerts WHERE active = 1"
    ).fetchall()
    conn.close()
    return [Alert(id=r[0], chat_id=r[1], asset=r[2], operator=r[3], target_value=r[4], active=bool(r[5])) for r in rows]


def deactivate_alert(alert_id: int, db_path: str = DB_PATH) -> None:
    """Marca una alerta como inactiva (ya se cumplió o el usuario la borró)."""
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE alerts SET active = 0 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()


def alert_is_triggered(alert: Alert, current_price: float) -> bool:
    """Evalúa si una alerta se cumple dado el precio actual."""
    if alert.operator == "<":
        return current_price < alert.target_value
    elif alert.operator == ">":
        return current_price > alert.target_value
    return False
