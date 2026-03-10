import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono pliku: {path}")

src = path.read_text(encoding="utf-8")

# backup
bak = path.with_suffix(path.suffix + ".bak_fix_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# znajd blok context menu (dodany wczeniej)
menu_pat = re.compile(r"\n\s*<!-- Context Menu \(prawy klik\) -->\s*\n.*?\n</div>\s*\n", re.DOTALL)
menu_m = menu_pat.search(out)

if not menu_m:
    raise SystemExit("Nie znalazem bloku 'Context Menu (prawy klik)'. Nic do naprawy albo blok ma inny ksztat.")

menu_block = menu_m.group(0)

# usu blok z aktualnego miejsca
out_wo_menu = out[:menu_m.start()] + out[menu_m.end():]

# wstaw menu ZA </script> (pierwsze zamknicie skryptu od koca)
script_close = out_wo_menu.rfind("</script>")
if script_close == -1:
    raise SystemExit("Nie znalazem </script> w vq_matrix.html — nie wiem gdzie wstawi menu.")

insert_at = script_close + len("</script>")
out_fixed = out_wo_menu[:insert_at] + menu_block + out_wo_menu[insert_at:]

# sanity: upewnij si, e menu jest PO </script>, a nie przed
pos_menu = out_fixed.find("<!-- Context Menu (prawy klik) -->")
pos_script = out_fixed.rfind("</script>", 0, pos_menu)
if pos_script != -1:
    # menu nadal przed </script> => co nietypowego
    raise SystemExit("Menu nadal znajduje si przed </script>. Podelij kocówk pliku, bo struktura jest inna.")

path.write_text(out_fixed, encoding="utf-8")
print("OK: przeniesiono Context Menu poza <script>.")
print("Zapisano:", path)
