import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono pliku: {path}")

src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_jsfix_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

# znajd wszystkie <script ...> ... </script> i napraw w rodku
script_pat = re.compile(r"(<script\b[^>]*>)(.*?)(</script>)", re.IGNORECASE | re.DOTALL)

def fix_script(body: str) -> tuple[str, int]:
    lines = body.splitlines(True)
    changed = 0
    fixed = []
    for ln in lines:
        if ln.lstrip().startswith("<"):
            # to jest HTML wklejony do JS -> komentujemy
            fixed.append("// [AUTO-FIX] " + ln)
            changed += 1
        else:
            fixed.append(ln)
    return "".join(fixed), changed

total_changed = 0

def repl(m: re.Match):
    global total_changed
    open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)
    new_body, ch = fix_script(body)
    total_changed += ch
    return open_tag + new_body + close_tag

out = script_pat.sub(repl, src)

Path("app/web/templates/vq_matrix.html").write_text(out, encoding="utf-8")
print("OK: zakomentowano linie HTML wewntrz <script>:", total_changed)
print("Zapisano:", path)
