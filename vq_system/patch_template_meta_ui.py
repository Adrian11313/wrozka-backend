import re
from pathlib import Path
from datetime import datetime

path = Path("app/web/templates/vq_matrix.html")
if not path.exists():
    raise SystemExit(f"Nie znaleziono pliku: {path}")

src = path.read_text(encoding="utf-8")

bak = path.with_suffix(path.suffix + ".bak_meta_ui_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
bak.write_text(src, encoding="utf-8")
print("Backup:", bak)

out = src

# ---------------- 1) CSS (kolory + badge + modal fields + attachments) ----------------
if "/* META_UI_PATCH */" not in out:
    css_block = """
  /* META_UI_PATCH */
  .cellbadges{margin:6px 0 6px 0;}
  .statusBadge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:700;margin-right:6px;}
  .badgeSmall{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;background:#eee;margin-right:6px;}
  .photoMark{font-size:12px;margin-left:6px;opacity:0.85;}

  /* delikatne ta jak prosie */
  td.cell.status_OK{background:rgba(0,160,0,0.10);}
  td.cell.status_RYZYKO{background:rgba(255,140,0,0.12);}
  td.cell.status_BLOKADA{background:rgba(220,0,0,0.12);}
  td.cell.status_DECYZJA{background:rgba(0,90,255,0.10);}

  .status_OK .statusBadge{background:rgba(0,160,0,0.20);}
  .status_RYZYKO .statusBadge{background:rgba(255,140,0,0.25);}
  .status_BLOKADA .statusBadge{background:rgba(220,0,0,0.25);}
  .status_DECYZJA .statusBadge{background:rgba(0,90,255,0.22);}

  .modalRow{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0;}
  .modalRow label{font-size:12px;color:#555;display:block;margin-bottom:4px;}
  .modalRow .f{min-width:160px;}
  .modalRow select,.modalRow input{padding:8px;border-radius:8px;border:1px solid #ccc;}
  .attList a{display:block;margin:4px 0;font-size:12px;}
"""
    # spróbuj wstawi pod pierwszym <style>
    out2 = out.replace("<style>", "<style>\n" + css_block, 1)
    if out2 == out:
        raise SystemExit("Nie znalazem <style> – nie wiem gdzie dopi CSS.")
    out = out2
    print("OK: dopito CSS (META_UI_PATCH)")
else:
    print("SKIP: CSS ju jest")

# ---------------- 2) data-* na TD (status/priority/owner/due_date/attachments_count) ----------------
# Szukamy td.cell w ptli i dopinamy atrybuty jeli brak
if "data-status" not in out:
    def add_attrs(m):
        td = m.group(0)
        insert = (
            '            data-status="{{ (p.status if p else \'\')|e }}"\n'
            '            data-priority="{{ (p.priority if p else \'\')|e }}"\n'
            '            data-owner="{{ (p.owner if p else \'\')|e }}"\n'
            '            data-due-date="{{ (p.due_date if p else \'\')|e }}"\n'
            '            data-attachments-count="{{ (p.attachments_count if p else 0) }}"\n'
        )
        # wstawiamy przed data-version (jest zawsze)
        if "data-version" in td:
            return td.replace("data-version", insert + "            data-version", 1)
        return td

    out2 = re.sub(r"<td class=\"cell\"[\s\S]*?data-version=", add_attrs, out, count=1)
    out = out2
    print("OK: dopito data-* na td.cell")
else:
    print("SKIP: data-* ju s")

# ---------------- 3) placeholder na badge (cellbadges) ----------------
if "class=\"cellbadges\"" not in out:
    # wstawiamy div po cellmeta w komórce
    out2 = re.sub(
        r'(<div class="cellmeta"[\s\S]*?</div>\s*)',
        r'\1<div class="cellbadges"></div>\n',
        out,
        count=1
    )
    out = out2
    print("OK: dodano <div class='cellbadges'>")
else:
    print("SKIP: cellbadges ju jest")

# ---------------- 4) Modal: dodaj pola status/prio/owner/due + upload ----------------
if "id=\"modalStatus\"" not in out:
    marker = '<textarea id="modalText" style="width:100%; min-height:200px;"></textarea>'
    if marker not in out:
        raise SystemExit("Nie znalazem textarea modalText – struktura modala jest inna.")
    modal_insert = """
    <div class="modalRow">
      <div class="f"><label>Status</label>
        <select id="modalStatus">
          <option value="">—</option>
          <option value="OK">OK</option>
          <option value="RYZYKO">RYZYKO</option>
          <option value="BLOKADA">BLOKADA</option>
          <option value="DECYZJA">DECYZJA</option>
        </select>
      </div>

      <div class="f"><label>Priorytet</label>
        <select id="modalPriority">
          <option value="">—</option>
          <option value="P1">P1</option>
          <option value="P2">P2</option>
          <option value="P3">P3</option>
        </select>
      </div>

      <div class="f"><label>Owner</label>
        <input id="modalOwner" type="text" placeholder="np. Janek"/>
      </div>

      <div class="f"><label>Termin</label>
        <input id="modalDue" type="date"/>
      </div>
    </div>
"""
    att_insert = """
    <div class="modalRow">
      <div class="f" style="min-width:320px;">
        <label>Dodaj zdjcie</label>
        <input id="modalPhoto" type="file" accept="image/*"/>
        <div id="modalAtt" class="attList"></div>
      </div>
    </div>
"""
    out = out.replace(marker, modal_insert + marker + att_insert, 1)
    print("OK: dopito pola modala + upload")
else:
    print("SKIP: modal fields ju s")

# ---------------- 5) JS: zmienne + helpery + integracja w openModal/save/init ----------------
if "function applyCellDecor" not in out:
    # dopnij zmienne po modalText
    out2 = out.replace(
        '  var modalText = document.getElementById("modalText");',
        '  var modalText = document.getElementById("modalText");\n'
        '  var modalStatus = document.getElementById("modalStatus");\n'
        '  var modalPriority = document.getElementById("modalPriority");\n'
        '  var modalOwner = document.getElementById("modalOwner");\n'
        '  var modalDue = document.getElementById("modalDue");\n'
        '  var modalPhoto = document.getElementById("modalPhoto");\n'
        '  var modalAtt = document.getElementById("modalAtt");\n',
        1
    )
    if out2 == out:
        raise SystemExit("Nie znalazem miejsca z var modalText – nie mog dopi JS.")
    out = out2

    helper = """
  // META_UI_PATCH: dekorowanie komórki (kolor + badge)
  function applyCellDecor(cell){
    if (!cell) return;
    var st = (cell.getAttribute("data-status") || "").trim();
    cell.classList.remove("status_OK","status_RYZYKO","status_BLOKADA","status_DECYZJA");
    if (st) cell.classList.add("status_" + st);

    var badges = cell.getElementsByClassName("cellbadges")[0];
    if (!badges) return;

    var pr = (cell.getAttribute("data-priority") || "").trim();
    var ow = (cell.getAttribute("data-owner") || "").trim();
    var dd = (cell.getAttribute("data-due-date") || "").trim();
    var ac = parseInt(cell.getAttribute("data-attachments-count") || "0", 10) || 0;

    var html = "";
    if (st) html += "<span class='statusBadge'>" + escapeHtml(st) + "</span>";
    if (pr) html += "<span class='badgeSmall'>" + escapeHtml(pr) + "</span>";
    if (ow) html += "<span class='badgeSmall'>" + escapeHtml(ow) + "</span>";
    if (dd) html += "<span class='badgeSmall'>" + escapeHtml(dd) + "</span>";
    if (ac > 0) html += "<span class='photoMark'>📷" + ac + "</span>";

    badges.innerHTML = html;
  }

  // META_UI_PATCH: lista zdj w modalu
  function loadAttachmentsToModal(topicId, depId){
    if (!modalAtt) return;
    modalAtt.innerHTML = "";
    xhr("GET", "/web/positions/attachments/by_cell/" + topicId + "/" + depId, null, null, function(status, text){
      if (!(status >= 200 && status < 300)) return;
      var items = [];
      try { items = text ? JSON.parse(text) : []; } catch(e) { items = []; }

      if (!items.length){
        modalAtt.innerHTML = "<div style='font-size:12px;color:#777;'>Brak zdj</div>";
        return;
      }

      var html = "";
      for (var i=0; i<items.length; i++){
        var it = items[i];
        var nm = it.original_name || ("zdjecie_" + it.id);
        html += "<a href='" + escapeHtml(it.url) + "' target='_blank'>📷 " + escapeHtml(nm) + "</a>";
      }
      modalAtt.innerHTML = html;
    });
  }

  // META_UI_PATCH: upload zdjcia po zapisie
  function uploadPhoto(topicId, depId, cb){
    if (!modalPhoto || !modalPhoto.files || !modalPhoto.files.length){
      if (cb) cb();
      return;
    }

    var fd = new FormData();
    fd.append("topic_id", topicId);
    fd.append("department_id", depId);
    fd.append("file", modalPhoto.files[0]);

    var r = new XMLHttpRequest();
    r.open("POST", "/web/positions/attachments/upload", true);
    r.onreadystatechange = function(){
      if (r.readyState !== 4) return;

      try {
        if (r.status >= 200 && r.status < 300){
          var resp = JSON.parse(r.responseText || "{}");
          if (currentCell && resp.attachments_count !== undefined){
            currentCell.setAttribute("data-attachments-count", String(resp.attachments_count));
          }
          modalPhoto.value = "";
        }
      } catch(e) {}

      if (cb) cb();
    };
    r.send(fd);
  }
"""
    out = out.replace("  // -------- EDIT MODAL ----------", helper + "\n  // -------- EDIT MODAL ----------", 1)
    print("OK: dopito helpery JS (applyCellDecor + attachments)")

else:
    print("SKIP: applyCellDecor ju jest")

# openModal: ustaw wartoci pól + load attachments
if "loadAttachmentsToModal(topicId, depId);" not in out:
    out = out.replace(
        '        modalText.value = cell.getAttribute("data-content") || "";',
        '        modalText.value = cell.getAttribute("data-content") || "";\n'
        '        if (modalStatus) modalStatus.value = (p && p.status) ? p.status : "";\n'
        '        if (modalPriority) modalPriority.value = (p && p.priority) ? p.priority : "";\n'
        '        if (modalOwner) modalOwner.value = (p && p.owner) ? p.owner : "";\n'
        '        if (modalDue) modalDue.value = (p && p.due_date) ? p.due_date : "";\n'
        '        loadAttachmentsToModal(topicId, depId);\n',
        1
    )
    print("OK: openModal uzupenia pola + aduje zdjcia")

# btnSave: dopisz pola do body
if "&status=" not in out:
    out = out.replace(
        '+ "&client_version=" + encodeURIComponent(clientVersion);',
        '+ "&client_version=" + encodeURIComponent(clientVersion)\n'
        '      + "&status=" + encodeURIComponent((modalStatus && modalStatus.value) ? modalStatus.value : "")\n'
        '      + "&priority=" + encodeURIComponent((modalPriority && modalPriority.value) ? modalPriority.value : "")\n'
        '      + "&owner=" + encodeURIComponent((modalOwner && modalOwner.value) ? modalOwner.value : "")\n'
        '      + "&due_date=" + encodeURIComponent((modalDue && modalDue.value) ? modalDue.value : "");',
        1
    )
    print("OK: btnSave wysya status/priority/owner/due_date")

# po sukcesie: ustaw data-* i applyCellDecor + uploadPhoto
if 'currentCell.setAttribute("data-status"' not in out:
    out = out.replace(
        '      currentCell.setAttribute("data-content", p.content || "");',
        '      currentCell.setAttribute("data-content", p.content || "");\n'
        '      currentCell.setAttribute("data-status", p.status || "");\n'
        '      currentCell.setAttribute("data-priority", p.priority || "");\n'
        '      currentCell.setAttribute("data-owner", p.owner || "");\n'
        '      currentCell.setAttribute("data-due-date", p.due_date || "");\n'
        '      if (p.attachments_count !== undefined) currentCell.setAttribute("data-attachments-count", String(p.attachments_count));\n',
        1
    )
    print("OK: po zapisie ustawiamy data-* meta")

if "applyCellDecor(currentCell);" not in out:
    out = out.replace(
        '      metaDiv.innerHTML = "v" + p.version;',
        '      metaDiv.innerHTML = "v" + p.version;\n'
        '      applyCellDecor(currentCell);\n'
        '      uploadPhoto(topicId, departmentId, function(){\n'
        '        applyCellDecor(currentCell);\n'
        '        loadAttachmentsToModal(topicId, departmentId);\n'
        '      });',
        1
    )
    print("OK: po zapisie applyCellDecor + uploadPhoto")

# init: applyCellDecor dla wszystkich komórek na starcie
if "META_UI_PATCH_INIT" not in out:
    out = out.replace(
        "  bindCells();",
        "  // META_UI_PATCH_INIT: ustaw kolory + badge na starcie\n"
        "  (function(){\n"
        "    var cells = document.getElementsByClassName('cell');\n"
        "    for (var i=0; i<cells.length; i++) applyCellDecor(cells[i]);\n"
        "  })();\n"
        "  bindCells();",
        1
    )
    print("OK: init applyCellDecor na starcie")

path.write_text(out, encoding="utf-8")
print("DONE:", path)
