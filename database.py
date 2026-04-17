import os
import json
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
                arquivo_path TEXT,
                texto_gerado TEXT,
                requisitos TEXT,
                beneficios TEXT,
                comentarios TEXT
            )
            """
        )
        # Migrations para colunas novas
        cursor = conn.execute("PRAGMA table_info(candidaturas)")
        colunas = [row[1] for row in cursor.fetchall()]
        novas = {
            "texto_gerado": "TEXT",
            "requisitos": "TEXT",
            "beneficios": "TEXT",
            "comentarios": "TEXT",
        }
        for col, tipo in novas.items():
            if col not in colunas:
                conn.execute(
                    f"ALTER TABLE candidaturas "
                    f"ADD COLUMN {col} {tipo}"
                )
        conn.close()

    def add_candidatura(
        self,
        empresa,
        cargo,
        status,
        arquivo,
        texto_gerado="",
        requisitos="",
        beneficios="",
    ):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO candidaturas "
            "(data, empresa, cargo, status, arquivo_path, "
            "texto_gerado, requisitos, beneficios) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (
                datetime.now().strftime("%Y-%m-%d"),
                empresa,
                cargo,
                status,
                arquivo,
                texto_gerado,
                requisitos,
                beneficios,
            ),
        )
        conn.commit()
        conn.close()

    def check_duplicata(self, empresa, cargo):
        """Retorna True se já existe candidatura."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM candidaturas "
            "WHERE LOWER(empresa) = LOWER(?) "
            "AND LOWER(cargo) = LOWER(?)",
            (empresa, cargo),
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def get_df(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql("SELECT * FROM candidaturas", conn)
        conn.close()
        return df

    def get_pendentes_followup(self, dias=7):
        """Candidaturas 'Enviado' há mais de N dias."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(
            "SELECT * FROM candidaturas "
            "WHERE status LIKE '%Enviado%' "
            "AND date(data) <= date('now', ?)",
            conn,
            params=(f"-{dias} days",),
        )
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

    def update_comentario(self, id_reg, comentario):
        """Atualiza o comentário de uma candidatura."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "UPDATE candidaturas SET comentarios = ? "
            "WHERE id = ?",
            (comentario, id_reg),
        )
        conn.commit()
        conn.close()

    def delete_reg(self, id_reg):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "DELETE FROM candidaturas WHERE id = ?",
            (id_reg,),
        )
        conn.commit()
        conn.close()

    def get_stats_semana(self, semanas_atras=0):
        """Stats de uma semana (0=atual, 1=anterior)."""
        from datetime import timedelta

        hoje = datetime.now()
        inicio = hoje - timedelta(
            days=hoje.weekday() + (semanas_atras * 7)
        )
        inicio = inicio.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        fim = inicio + timedelta(days=7)

        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(
            "SELECT * FROM candidaturas "
            "WHERE date(data) >= date(?) "
            "AND date(data) < date(?)",
            conn,
            params=(
                inicio.strftime("%Y-%m-%d"),
                fim.strftime("%Y-%m-%d"),
            ),
        )
        conn.close()

        total = len(df)
        entrevistas = len(
            df[df["status"] == "Entrevista"]
        )
        return {"total": total, "entrevistas": entrevistas}

    def get_skills_ranking(self):
        """Agrega requisitos de todas as vagas e retorna ranking."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(
            "SELECT requisitos FROM candidaturas "
            "WHERE requisitos IS NOT NULL "
            "AND requisitos != ''",
            conn,
        )
        conn.close()

        skills_count = {}
        for row in df["requisitos"]:
            try:
                lista = json.loads(row)
                if isinstance(lista, list):
                    for skill in lista:
                        s = skill.strip().lower()
                        if s:
                            skills_count[s] = (
                                skills_count.get(s, 0) + 1
                            )
            except (json.JSONDecodeError, TypeError):
                continue

        ranking = sorted(
            skills_count.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return pd.DataFrame(
            ranking, columns=["Skill", "Frequência"]
        )
