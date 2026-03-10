import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_fix_js_after_script_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

# znajd </script>
script_close = src.find("</script>")
if script_close == -1:
    raise SystemExit("Nie ma </script> w pliku.")

before = src[:script_close]
after = src[script_close+len("</script>"):]

# jeli po </script> jest JS (context menu itp.) – przenie go do rodka skryptu
m = re.search(r"(//\s*-+\s*CONTEXT MENU.*|var\s+ctxMenu\s*=|function\s+openContextMenu\s*\(|function\s+restoreFromHistory\s*\()", after)
if not m:
    print("INFO: Nie widz JS po </script> – nic nie przenosz.")
    raise SystemExit("DONE (nic do zmiany).")

js_tail = after[m.start():]

# usu ten JS z "after"
after_clean = after[:m.start()]

# wyczy przypadkowe templaty/HTML na kocu
# (zostawiamy tylko whitespace i bloki Jinja)
after_clean = re.sub(r"\s+$", "\n", after_clean)

# dopnij przeniesiony JS do wntrza <script> (przed </script>)
fixed = before.rstrip() + "\n\n" + js_tail.strip() + "\n</script>" + after_clean

path.write_text(fixed, encoding="utf-8")
print("OK: przeniesiono JS z koca pliku do wntrza <script>.")
print("Zapisano:", path)
print("DONE")
