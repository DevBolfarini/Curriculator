import os
import sqlite3
from datetime import datetime

import pandas as pd


class DatabaseManager:
    def __init__(self, db_path="controle_dados/candidaturas.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs("controle_dados", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidaturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                empresa TEXT,
                cargo TEXT,
                status TEXT,
                arquivo_path TEXT
            )
            """
        )
        conn.close()

    def add_candidatura(self, empresa, cargo, status, arquivo):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO candidaturas "
            "(data, empresa, cargo, status, arquivo_path) "
            "VALUES (?,?,?,?,?)",
            (
                datetime.now().strftime("%Y-%m-%d"),
                empresa,
                cargo,
                status,
                arquivo,
            ),
        )
        conn.commit()
        conn.close()

    def get_df(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM candidaturas", conn)
        conn.close()
        return df

    def update_status(self, id_reg, novo_status):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE candidaturas SET status = ? WHERE id = ?",
            (novo_status, id_reg),
        )
        conn.commit()
        conn.close()

    def delete_reg(self, id_reg):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM candidaturas WHERE id = ?", (id_reg,))
        conn.commit()
        conn.close()
