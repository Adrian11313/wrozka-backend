import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_fix_brace_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) usu doklejony blok tooltip functions po IIFE (po })();)
out = re.sub(
    r"\)\s*;\s*\}\)\s*\(\)\s*;\s*(?:\r?\n)+\s*//\s*--- Tooltip positioning.*?function\s+showTip\s*\(cell\)\s*\{.*?\}\s*(?:\r?\n)+",
    "})();\n\n",
    out,
    flags=re.DOTALL
)

# 2) usu osierocony fragment starego enableColumnResize (z ths[i])
out = re.sub(
    r"\s*function\s+onUp\s*\(\)\s*\{\s*document\.removeEventListener\(\"mousemove\",\s*onMove\);\s*document\.removeEventListener\(\"mouseup\",\s*onUp\);\s*document\.body\.classList\.remove\(\"resizing\"\);\s*\}\s*document\.addEventListener\(\"mousemove\",\s*onMove\);\s*document\.addEventListener\(\"mouseup\",\s*onUp\);\s*\}\);\s*\}\)\(ths\[i\]\);\s*\}\s*\}\s*",
    "\n",
    out,
    flags=re.DOTALL
)

# 3) sanity: upewnij si e mamy tylko jedno </script> w tym miejscu i e ctxMenu jest po </script>
if out.count("</script>") < 1:
    raise SystemExit("Po patchu znikno </script> - co jest nie tak.")

path.write_text(out, encoding="utf-8")
print("OK: usunito duplikaty tooltip + osierocony fragment ths[i].")
print("Zapisano:", path)
print("DONE")
