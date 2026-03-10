from pathlib import Path
import sqlite3
from datetime import datetime
DB_PATH = Path("vq.db")  # sqlite:///./vq.db
if not DB_PATH.exists():
    raise SystemExit(f"Nie znaleziono bazy: {DB_PATH.resolve()}")
bak = DB_PATH.with_suffix(".db.bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_bytes(DB_PATH.read_bytes())
print("Backup DB:", bak)
con = sqlite3.connect(str(DB_PATH))
cur = con.cursor()
def cols(table):
    cur.execute(f"PRAGMA table_info({table})")
    return {r[1] for r in cur.fetchall()}
def add_col(table, name, ddl):
    if name in cols(table):
        print(f"OK: {table}.{name} już istnieje")
        return
    cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
    print(f"Dodano: {table}.{name} {ddl}")
# positions
for name, ddl in [
    ("status", "TEXT"),
    ("priority", "TEXT"),
    ("owner", "TEXT"),
    ("due_date", "TEXT"),
]:
    add_col("positions", name, ddl)
# position_history
for name, ddl in [
    ("old_status", "TEXT"),
    ("new_status", "TEXT"),
    ("old_priority", "TEXT"),
    ("new_priority", "TEXT"),
    ("old_owner", "TEXT"),
    ("new_owner", "TEXT"),
    ("old_due_date", "TEXT"),
    ("new_due_date", "TEXT"),
]:
    add_col("position_history", name, ddl)
# attachments table
cur.execute("""
CREATE TABLE IF NOT EXISTS position_attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  position_id INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  original_name TEXT,
  mime_type TEXT,
  uploaded_by INTEGER,
  uploaded_at TEXT,
  FOREIGN KEY(position_id) REFERENCES positions(id)
)
""")
print("OK: tabela position_attachments (jeśli nie było)")
con.commit()
con.close()
print("DONE")
