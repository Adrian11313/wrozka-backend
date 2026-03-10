import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono pliku: {path}")

src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_ctxmenu_list_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# 1) Dopisz CSS dla scrolla w ctxMenu/ctxItems (jeli nie ma)
css_add = r"""
  /* Context menu container */
  #ctxMenu { max-height: 360px; overflow: hidden; }
  #ctxItems { max-height: 300px; overflow: auto; padding-right: 4px; }
"""
if "#ctxItems" not in out:
    # wstawiamy tu po .ctxTxt jeli znajdziemy
    m = re.search(r"\.ctxTxt\s*\{[^}]*\}\s*", out)
    if m:
        out = out[:m.end()] + css_add + out[m.end():]
        print("OK: dopisano CSS dla #ctxMenu/#ctxItems.")
    else:
        print("WARN: nie znalazem miejsca na CSS, pomijam dopisanie (rcznie moesz wklei w <style>).")
else:
    print("OK: CSS dla #ctxItems ju istnieje (pomijam).")

# 2) Podmie openContextMenu(...) na wersj listujc wpisy
pattern = re.compile(
    r"function\s+openContextMenu\s*\(\s*cell\s*,\s*x\s*,\s*y\s*\)\s*\{.*?\n\s*\}\n\n\s*function\s+restoreFromHistory\s*\(",
    re.DOTALL
)

m = pattern.search(out)
if not m:
    raise SystemExit("Nie znalazem caej funkcji openContextMenu(...) (albo ma inny ksztat). Wklej mi j wtedy rcznie, dopasuj patch.")

replacement_open = r"""function openContextMenu(cell, x, y) {
    if (!ensureCtxEls()) return;
    if (!ctxMenu) return;

    // blokuj tooltipy gdy menu otwarte
    if (typeof ctxOpen !== "undefined") ctxOpen = true;
    if (typeof hideAllTips === "function") hideAllTips();

    var topicId = cell.getAttribute("data-topic-id");
    var depId = cell.getAttribute("data-department-id");
    var depName = cell.getAttribute("data-department-name") || "";

    ctxTitle.innerHTML = "Historia • " + escapeHtml(depName);
    ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>adowanie...</div>";
    ctxMenu.style.display = "block";

    // pozycja menu (eby nie wyjechao poza ekran)
    var w = 380;
    var h = 360;
    var px = Math.min(x, window.innerWidth - w - 10);
    var py = Math.min(y, window.innerHeight - h - 10);
    ctxMenu.style.left = px + "px";
    ctxMenu.style.top = py + "px";

    xhr("GET", "/web/positions/history/by_cell/" + topicId + "/" + depId, null, null, function(status, text){
      if (status === 401) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Zaloguj si.</div>";
        return;
      }
      if (!(status >= 200 && status < 300)) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Bd: " + status + "</div>";
        return;
      }

      // zabezpieczenie gdy backend zwróci HTML
      if (!text || text.trim().startsWith("<")) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Niepoprawna odpowied serwera.</div>";
        return;
      }

      var items = [];
      try { items = text ? JSON.parse(text) : []; } catch(e) { items = []; }

      if (!items.length) {
        ctxItems.innerHTML = "<div style='color:rgba(255,255,255,0.75);'>Brak historii.</div>";
        return;
      }

      // lista wpisów do przywrócenia (do 10)
      var html = "";
      for (var i=0; i<items.length && i<10; i++) {
        var it = items[i];
        var meta = "v" + it.new_version + " • " + formatDate(it.changed_at) + " • user_id=" + it.changed_by;
        var txt = (it.new_content && it.new_content.length) ? it.new_content : "(pusto)";
        html += "<div class='ctxItem' data-hid='" + it.id + "'>"
          +   "<div class='ctxMeta'>" + escapeHtml(meta) + "</div>"
          +   "<div class='ctxTxt'>" + escapeHtml(txt) + "</div>"
          + "</div>";
      }
      ctxItems.innerHTML = html;

      var els = ctxItems.getElementsByClassName("ctxItem");
      for (var j=0; j<els.length; j++) {
        (function(el){
          el.onclick = function(ev){
            ev.stopPropagation();
            var hid = el.getAttribute("data-hid");
            restoreFromHistory(cell, hid);
            closeContextMenu();
          };
        })(els[j]);
      }
    });
  }

  function restoreFromHistory("""
out = out[:m.start()] + replacement_open + out[m.end()-len("function restoreFromHistory("):]

print("OK: podmieniono openContextMenu() na list wpisów.")

# 3) Upewnij si, e closeContextMenu ustawia ctxOpen=false
# (jeli masz closeContextMenu bez ctxOpen, dopiszemy w rodku)
close_pat = re.compile(r"function\s+closeContextMenu\s*\(\s*\)\s*\{\s*(.*?)\n\s*\}", re.DOTALL)
cm = close_pat.search(out)
if cm:
    body = cm.group(1)
    if "ctxOpen" not in body:
        new_body = body + "\n    if (typeof ctxOpen !== 'undefined') ctxOpen = false;"
        out = out[:cm.start(1)] + new_body + out[cm.end(1):]
        print("OK: dopisano ctxOpen=false w closeContextMenu().")
    else:
        print("OK: closeContextMenu ju obsuguje ctxOpen (pomijam).")
else:
    print("WARN: nie znalazem closeContextMenu() - pomijam ctxOpen=false.")

path.write_text(out, encoding="utf-8")
print("Zapisano:", path)
print("DONE")
