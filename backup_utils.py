#!/usr/bin/env python3
"""
🔄 Utilitário de Backup/Restore para Banco de Dados SQLite

Uso local:
  python backup_utils.py backup     # Faz backup do banco
  python backup_utils.py restore    # Restaura do backup

No Streamlit Cloud, adicione no app.py:
  from backup_utils import auto_backup
  auto_backup()
"""

import os
import shutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path


class BackupManager:
    def __init__(
        self,
        db_path="controle_dados/candidaturas.db",
        backup_dir="controle_dados/backups",
    ):
        self.db_path = db_path
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)

    def backup(self, description=""):
        """Faz backup do banco de dados"""
        if not os.path.exists(self.db_path):
            print(f"❌ Banco de dados não encontrado: {self.db_path}")
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        try:
            shutil.copy2(self.db_path, backup_path)
            
            # Salvar metadados
            metadata = {
                "timestamp": timestamp,
                "description": description,
                "database_size": os.path.getsize(self.db_path),
            }
            
            metadata_path = os.path.join(
                self.backup_dir, f"backup_{timestamp}.json"
            )
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Backup criado: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Erro ao fazer backup: {e}")
            return False

    def restore(self, backup_filename):
        """Restaura banco de dados de um backup"""
        backup_path = os.path.join(self.backup_dir, backup_filename)

        if not os.path.exists(backup_path):
            print(f"❌ Backup não encontrado: {backup_path}")
            return False

        try:
            # Criar backup do banco atual antes de sobrescrever
            if os.path.exists(self.db_path):
                self.backup(description="Before restore")

            shutil.copy2(backup_path, self.db_path)
            print(f"✅ Banco restaurado de: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Erro ao restaurar: {e}")
            return False

    def list_backups(self):
        """Lista todos os backups disponíveis"""
        backups = sorted(
            [
                f for f in os.listdir(self.backup_dir)
                if f.endswith(".db")
            ],
            reverse=True,
        )

        if not backups:
            print("📭 Nenhum backup encontrado")
            return []

        print(f"📦 {len(backups)} backup(s) disponível(is):\n")
        for i, backup in enumerate(backups, 1):
            backup_path = os.path.join(self.backup_dir, backup)
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            print(f"  {i}. {backup} ({size_mb:.2f} MB)")

        return backups

    def prune_old_backups(self, keep_count=10):
        """Remove backups antigos, mantendo apenas os últimos N"""
        backups = sorted(
            [
                f for f in os.listdir(self.backup_dir)
                if f.endswith(".db")
            ],
            reverse=True,
        )

        if len(backups) > keep_count:
            to_remove = backups[keep_count:]
            for backup in to_remove:
                backup_path = os.path.join(self.backup_dir, backup)
                os.remove(backup_path)
                
                # Remover metadados também
                json_path = backup_path.replace(".db", ".json")
                if os.path.exists(json_path):
                    os.remove(json_path)

            print(
                f"✅ Removidos {len(to_remove)} backup(s) antigo(s)"
            )


def auto_backup():
    """
    Função para ser chamada no Streamlit Cloud
    Faz backup automático a cada inicialização
    """
    import streamlit as st

    manager = BackupManager()

    # Não fazer backup a cada rerun, apenas uma vez
    if "backup_feito" not in st.session_state:
        try:
            manager.backup(description="Auto-backup on app start")
            st.session_state.backup_feito = True
        except Exception as e:
            st.warning(f"⚠️ Não foi possível fazer backup automático: {e}")


if __name__ == "__main__":
    import sys

    manager = BackupManager()

    if len(sys.argv) < 2:
        print("Uso: python backup_utils.py [backup|restore|list|prune]")
        sys.exit(1)

    comando = sys.argv[1].lower()

    if comando == "backup":
        desc = sys.argv[2] if len(sys.argv) > 2 else ""
        manager.backup(description=desc)

    elif comando == "restore":
        if len(sys.argv) < 3:
            print("Uso: python backup_utils.py restore <backup_filename>")
            manager.list_backups()
            sys.exit(1)
        manager.restore(sys.argv[2])

    elif comando == "list":
        manager.list_backups()

    elif comando == "prune":
        keep = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        manager.prune_old_backups(keep_count=keep)

    else:
        print(f"❌ Comando desconhecido: {comando}")
        sys.exit(1)
