from pathlib import Path
from datetime import datetime
import re
p = Path("app/web/vq_page.py")
if not p.exists():
    raise SystemExit(f"Brak pliku: {p}")
src = p.read_text(encoding="utf-8")
bak = p.with_suffix(".py.bak_fixsqlpath_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)
out = src
# 1) import Path
if "from pathlib import Path" not in out:
    # wstaw po innych importach na górze
    out = out.replace(
        "from sqlalchemy.orm import Session\n",
        "from sqlalchemy.orm import Session\nfrom pathlib import Path\n"
    )
    print("OK: dodano import Path")
# 2) każde db.execute("...") -> db.execute(text("..."))
#    (dotyczy SELECT COUNT, INSERT, SELECT list, SELECT get)
out2 = re.sub(
    r"db\.execute\(\s*\"([^\"]+)\"\s*,\s*({[\s\S]*?})\s*\)",
    r"db.execute(text(\"\1\"), \2)",
    out
)
# przypadek: db.execute("SELECT ...").scalar()
out2 = re.sub(
    r"db\.execute\(\s*\"([^\"]+)\"\s*,\s*({[\s\S]*?})\s*\)\.scalar\(\)",
    r"db.execute(text(\"\1\"), \2).scalar()",
    out2
)
# przypadek: db.execute("SELECT ...").fetchone()/fetchall()
out2 = re.sub(
    r"db\.execute\(\s*\"([^\"]+)\"\s*,\s*({[\s\S]*?})\s*\)\.fetch(one|all)\(\)",
    r"db.execute(text(\"\1\"), \2).fetch\1()",
    out2
)
# jeśli coś zostało niezmienione, a jest db.execute("SELECT ...") bez params, też opakuj w text()
out2 = re.sub(
    r"db\.execute\(\s*\"([^\"]+)\"\s*\)",
    r"db.execute(text(\"\1\"))",
    out2
)
p.write_text(out2, encoding="utf-8")
print("DONE: vq_page.py patched (Path + text())")
