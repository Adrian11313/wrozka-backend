import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono pliku: {path}")

src = path.read_text(encoding="utf-8")

# backup
bak = path.with_suffix(path.suffix + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) CSS: usu 'left: 6px;' z .tip (jeli jest)
# Robimy to bezpiecznie: tylko wewntrz bloku .tip { ... }
tip_block = re.search(r"(\.tip\s*\{)(.*?)(\})", out, flags=re.S)
if tip_block:
    before, body, after = tip_block.group(1), tip_block.group(2), tip_block.group(3)
    new_body = re.sub(r"^\s*left\s*:\s*6px\s*;\s*\r?\n", "", body, flags=re.M)
    # jeli 'left: 6px;' byo w jednej linii bez \n
    new_body = re.sub(r"\s*left\s*:\s*6px\s*;\s*", "\n", new_body)
    out = out[:tip_block.start()] + before + new_body + after + out[tip_block.end():]
else:
    print("UWAGA: nie znalazem bloku CSS '.tip { ... }' — pomijam usuwanie left")

# 2) JS: dodaj positionTip(cell) jeli nie istnieje
if "function positionTip(cell)" not in out:
    m = re.search(r"\n\s*function\s+showTip\s*\(\s*cell\s*\)\s*\{", out)
    if not m:
        raise SystemExit("Nie znalazem 'function showTip(cell)' w pliku — nie mog wstawi positionTip.")
    insert_at = m.start()

    position_tip = r'''
  function positionTip(cell) {
    var tip = cell.getElementsByClassName("tip")[0];
    if (!tip) return;

    tip.style.left = "";
    tip.style.right = "";

    tip.style.display = "block";

    var rect = tip.getBoundingClientRect();
    var pad = 10;

    if (rect.right > window.innerWidth - pad) {
      tip.style.left = "auto";
      tip.style.right = "6px";
    } else {
      tip.style.right = "auto";
      tip.style.left = "6px";
    }

    rect = tip.getBoundingClientRect();
    if (rect.left < pad) {
      tip.style.left = pad + "px";
      tip.style.right = "auto";
    }
  }
'''
    out = out[:insert_at] + position_tip + out[insert_at:]
    print("Dodano: function positionTip(cell)")
else:
    print("OK: function positionTip(cell) ju istnieje")

# 3) JS: showTip ma woa positionTip(cell)
# Podmie cae ciao showTip na poprawne, jeli znajdziemy funkcj
show_tip = re.search(r"function\s+showTip\s*\(\s*cell\s*\)\s*\{.*?\n\s*\}", out, flags=re.S)
if not show_tip:
    raise SystemExit("Nie znalazem definicji showTip(cell) — nie mog jej poprawi.")

show_tip_body = show_tip.group(0)

# Jeli ju ma positionTip(cell) to nic nie rób
if "positionTip(cell)" in show_tip_body:
    print("OK: showTip(cell) ju woa positionTip(cell)")
else:
    # Zastp funkcj showTip na wersj pewn
    replacement = r'''function showTip(cell) {
    var tip = cell.getElementsByClassName("tip")[0];
    if (!tip) return;
    tip.style.display = "block";
    positionTip(cell);
  }'''
    out = out[:show_tip.start()] + replacement + out[show_tip.end():]
    print("Zmieniono: showTip(cell) -> dodano positionTip(cell)")

path.write_text(out, encoding="utf-8")
print("Zapisano zmiany w:", path)
print("DONE")
