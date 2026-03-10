from pathlib import Path
from datetime import datetime
import re

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono: {path}")

src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_maxwidth_fix_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) Usu max-width ograniczajce wzrost w prawo (2 warianty zapisu)
out2 = re.sub(r"\bth\s*\{\s*max-width\s*:\s*260px\s*;\s*\}\s*", "", out)
out2 = re.sub(r"\btd\s*\{\s*max-width\s*:\s*260px\s*;\s*\}\s*", "", out2)

# Jeli zamiast tego jest jedna regua "th, td { max-width: 260px; }"
out2 = re.sub(r"\bth\s*,\s*td\s*\{\s*max-width\s*:\s*260px\s*;\s*\}\s*", "", out2)

if out2 == out:
    print("INFO: nie znalazem dokadnie 'max-width: 260px' w th/td (moe masz inn warto).")
out = out2

# 2) Dopisz override (na wszelki wypadek), eby na pewno nie byo limitu
if "/* [RESIZE] allow columns to grow */" not in out:
    add_css = """
  /* [RESIZE] allow columns to grow */
  th, td { max-width: none !important; }
"""
    out_css = re.sub(r"</style>", add_css + "\n</style>", out, count=1, flags=re.IGNORECASE)
    if out_css == out:
        raise SystemExit("Nie znalazem </style> – nie mam gdzie dopi CSS.")
    out = out_css
    print("OK: dopisano override CSS (max-width:none)")
else:
    print("Override CSS ju istnieje – pomijam")

# 3) (Opcjonalnie) Wrap tabeli w kontener przewijania, jeli go nie ma
if 'class="vqTableWrap"' not in out:
    # znajd pierwszy <table ...> i owi
    m = re.search(r"(<table\b[^>]*>)", out)
    if m:
        table_open = m.group(1)
        # wstaw div przed <table ...>
        out = out.replace(table_open, '<div class="vqTableWrap">' + "\n" + table_open, 1)
        # zamknij diva po pierwszym </table>
        out = out.replace("</table>", "</table>\n</div>", 1)

        # CSS dla wrappera
        wrap_css = """
  .vqTableWrap{
    max-width: 100%;
    overflow: auto;
  }
"""
        out2 = re.sub(r"</style>", wrap_css + "\n</style>", out, count=1, flags=re.IGNORECASE)
        if out2 != out:
            out = out2
        print("OK: dodano wrapper przewijania (.vqTableWrap)")
    else:
        print("INFO: nie znalazem <table> do owinicia – pomijam wrapper")

path.write_text(out, encoding="utf-8")
print("Zapisano:", path)
print("DONE")
