import re
from pathlib import Path
from datetime import datetime
def backup(p: Path):
    b = p.with_suffix(p.suffix + ".bak_meta_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    b.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
    print("Backup:", b)
def ensure_import_string(src: str) -> str:
    m = re.search(r"from sqlalchemy import ([^\n]+)", src)
    if not m:
        return src
    line = m.group(0)
    if "String" in line:
        return src
    return src.replace(line, line + ", String")
def ensure_field(src: str, field_line: str) -> str:
    if field_line.strip() in src:
        return src
    # wstaw po pierwszych atrybutach klasy (po __tablename__ zwykle)
    return re.sub(r"(class\s+\w+\(Base\):\s*\n(?:.*\n){0,20})", r"\1" + field_line + "\n", src, count=1)
# Position
pos = Path("app/models/position.py")
backup(pos)
s = pos.read_text(encoding="utf-8")
s = ensure_import_string(s)
s = ensure_field(s, "    status = Column(String)")
s = ensure_field(s, "    priority = Column(String)")
s = ensure_field(s, "    owner = Column(String)")
s = ensure_field(s, "    due_date = Column(String)")
pos.write_text(s, encoding="utf-8")
print("OK: Position fields")
# PositionHistory
hist = Path("app/models/position_history.py")
backup(hist)
h = hist.read_text(encoding="utf-8")
h = ensure_import_string(h)
for line in [
    "    old_status = Column(String)",
    "    new_status = Column(String)",
    "    old_priority = Column(String)",
    "    new_priority = Column(String)",
    "    old_owner = Column(String)",
    "    new_owner = Column(String)",
    "    old_due_date = Column(String)",
    "    new_due_date = Column(String)",
]:
    h = ensure_field(h, line)
hist.write_text(h, encoding="utf-8")
print("OK: PositionHistory fields")
