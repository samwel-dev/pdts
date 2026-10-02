"""
generate_structure_map.py

Draws a hierarchical tree map of the PDTS index.html file
and saves a high-resolution PNG (300 dpi) and a vector PDF to the Desktop.

Run from the PDTS_App folder:
  & "C:\\Users\\SAM\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe" generate_structure_map.py
"""

import os
import sys
import pathlib
import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


# ============================================================
# LOCATE index.html
# ============================================================
def find_index_html():
    candidates = [
        pathlib.Path("templates/index.html"),
        pathlib.Path("index.html"),
        pathlib.Path.home() / "OneDrive" / "Desktop" / "PDTS_App" / "templates" / "index.html",
        pathlib.Path.home() / "Desktop" / "PDTS_App" / "templates" / "index.html",
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    return None

INDEX = find_index_html()

if INDEX:
    size_kb = os.path.getsize(INDEX) / 1024
    lines = sum(1 for _ in open(INDEX, encoding="utf-8"))
    modified = datetime.datetime.fromtimestamp(os.path.getmtime(INDEX)).strftime("%Y-%m-%d %H:%M")
else:
    size_kb, lines, modified = 0, 0, "not found"


# ============================================================
# NODE DATA — (depth, text, type)
# ============================================================
# Types drive the styling. See TYPE_STYLE below.
NODES = [
    (0, "templates/index.html", "root"),

    # ---------- <head> ----------
    (1, "<head>", "section"),
    (2, "<meta> · <title> · Google Fonts imports", "item"),
    (2, "<style>  —  embedded CSS", "block"),
    (3, ":root { --navy, --teal, --red ... }  —  colour tokens", "css"),
    (3, "body, .wrap, header, nav  —  layout shell", "css"),
    (3, ".panel, .grid, .fld, .btn  —  form & panels", "css"),
    (3, ".modal, .stamp-box, .signature  —  print/consent", "css"),
    (3, "@media print { }  —  print-to-PDF rules", "css"),

    # ---------- <body> ----------
    (1, "<body>", "section"),
    (2, "<header>  —  brand bar with station name + Change Station link", "item"),
    (2, "<nav>  —  tabs: Triage Desk · Commander's View", "item"),

    (2, "<div class=\"wrap\">  —  page container", "block"),

    # ---------- Station selector ----------
    (3, "<div id=\"stationModal\">  —  station picker (opens on first load)", "item"),

    # ---------- v-desk ----------
    (3, "<div id=\"v-desk\">  —  Triage Desk view", "block"),

    (4, "<div id=\"p-intake\">  —  complaint intake form", "block"),
    (5, "Case Reference · Officer · Offence Category · Specific Offence", "leaf"),
    (5, "Value at Issue · Exact Age · Gender · Vulnerability Flag", "leaf"),
    (5, "Sub-County (auto) · Anonymous Informant checkbox", "leaf"),
    (5, "<div id=\"fld-adr-fields\">  —  ADR suitability block", "block"),
    (6, "Complainant Willingness  —  Article 50(9) refusal check", "hot"),
    (6, "Offender Behaviour · Prior History · Offender Willingness", "leaf"),
    (5, "Brief Description  —  names blocked by validation", "leaf"),

    (4, "<div id=\"p-triage\">  —  fallback triage questions", "block"),

    (4, "<div id=\"p-result\">  —  outcome screen", "block"),
    (5, "<div id=\"oc\">  —  coloured outcome card (6 route variants)", "leaf"),
    (5, "<div id=\"p-consent-actions\">  —  consent / referral / SMS / email", "leaf"),
    (5, "<div id=\"p-override\">  —  officer override (escalation only)", "leaf"),
    (5, "<div id=\"trail\">  —  decision trail: why this route", "leaf"),

    # ---------- v-dash ----------
    (3, "<div id=\"v-dash\">  —  Commander's View", "block"),
    (4, "14-Day Reminder panel  —  pending ADR reviews", "leaf"),
    (4, "Metric cards  —  total · diverted · rate · cost avoided", "leaf"),
    (4, "Routing breakdown bars  —  by route kind", "leaf"),
    (4, "Search bar  —  filter by ref, offence, officer", "leaf"),
    (4, "Log table  —  all records with pill-tagged routes", "leaf"),

    # ---------- consent modal ----------
    (3, "<div id=\"consentModal\">  —  printable consent form", "item"),

    # ---------- <script> ----------
    (1, "<script>  —  application logic", "section"),

    (2, "Configuration constants  —  API_URL, PER_DIEM, DAYS", "item"),
    (2, "Storage keys  —  DRAFT_KEY, OFFICER_KEY", "item"),
    (2, "H()  —  HTML escape helper (XSS guard)", "hot"),

    (2, "OFFENCE_TREE  —  9 offence categories", "block"),
    (3, "sexual · gbv · child · violent  (serious → Safeguard Gate)", "leaf"),
    (3, "economic · petty  (ADR-eligible with policy caps)", "leaf"),
    (3, "civil · traffic · other", "leaf"),

    (2, "LEGAL_KB  —  statute + office per civil offence", "item"),

    (2, "window.onload()  —  boot sequence + station modal", "item"),

    (2, "Station management", "block"),
    (3, "loadStations() · setStation() · openStationModal()", "leaf"),

    (2, "Draft autosave", "block"),
    (3, "saveDraft() · restoreDraft() · clearDraft()", "leaf"),

    (2, "Form handlers", "block"),
    (3, "onCategoryChange() · onDetailChange()", "leaf"),
    (3, "deriveAgeBand() · checkVulnerability()", "leaf"),

    (2, "API layer", "block"),
    (3, "fetchData() · addRecord()  —  fail-safe on HTTP error", "hot"),
    (3, "updateRecord()  —  URL-encoded ref", "leaf"),

    (2, "Utilities", "block"),
    (3, "refCode() · today() · addDays() · nowISO()", "leaf"),
    (3, "go() · loadDemo()", "leaf"),

    (2, "Routing engine", "block"),
    (3, "startTriage()  —  input validation + dispatch", "hot"),
    (3, "getAgeBand()  —  maps age to Children Act band", "leaf"),
    (3, "Q · render() · answer()  —  triage question fallback", "leaf"),
    (3, "R = { stop, formal, civil, adr, traffic }  —  route definitions", "hot"),
    (3, "finish(kind)  —  deep-clone route + persist + render", "hot"),

    (2, "Override & reset", "block"),
    (3, "submitOverride()  —  escalation-only, min 10 chars", "leaf"),
    (3, "resetDesk()  —  clear form, restore ref code", "leaf"),

    (2, "Dashboard", "block"),
    (3, "refresh()  —  recompute metrics, poll every 5s", "leaf"),
    (3, "renderLog(rows)  —  escaped HTML output", "leaf"),
    (3, "applySearch()  —  filter by ref / offence / officer", "leaf"),

    (2, "Consent & print", "block"),
    (3, "addParty()  —  dynamic complainant / respondent rows", "leaf"),
    (3, "generateConsent() · printConsent()", "leaf"),
    (3, "generateReferralLetter()  —  uses LEGAL_KB", "leaf"),
    (3, "closeModal() · sendSMS() · sendEmail()", "leaf"),

    (2, "Resolution", "block"),
    (3, "RESOLUTION_CATEGORIES  —  standardised outcomes", "leaf"),
    (3, "escalateCase() · markResolved()", "leaf"),

    (2, "Exports", "block"),
    (3, "exportCSV()  —  formula-injection guard", "leaf"),
    (3, "exportStationRegister()  —  policy data + offence breakdown", "leaf"),
    (3, "clearAll()  —  requires typing DELETE to confirm", "leaf"),
]


# ============================================================
# STYLING
# ============================================================
TYPE_STYLE = {
    "root":    {"color": "#1B3A5C", "weight": "bold",   "size": 18,  "style": "normal", "shape": "rounded"},
    "section": {"color": "#2E7D8E", "weight": "bold",   "size": 14,  "style": "normal", "shape": "rounded"},
    "block":   {"color": "#2B5D8A", "weight": "bold",   "size": 11.5,"style": "normal", "shape": "rect"},
    "item":    {"color": "#1f2a30", "weight": "normal", "size": 10,  "style": "normal", "shape": "none"},
    "leaf":    {"color": "#5a6a70", "weight": "normal", "size": 9.5, "style": "normal", "shape": "none"},
    "css":     {"color": "#8a6318", "weight": "normal", "size": 9,   "style": "italic", "shape": "none"},
    "hot":     {"color": "#A33232", "weight": "bold",   "size": 10.5,"style": "normal", "shape": "rect"},
}

# Column x-positions (inches)
X_TEXT  = [0.30, 1.05, 2.05, 3.20, 4.30, 5.60, 6.80]
X_GUIDE = [None, 0.90, 1.90, 3.05, 4.15, 5.45, 6.65]

ROW_H   = 0.34
FIG_W   = 15.0


# ============================================================
# FONT
# ============================================================
available = {f.name for f in fm.fontManager.ttflist}
for candidate in ["Segoe UI", "Calibri", "DejaVu Sans", "Arial"]:
    if candidate in available:
        plt.rcParams["font.family"] = candidate
        break


# ============================================================
# BUILD FIGURE
# ============================================================
n = len(NODES)
fig_h = n * ROW_H + 3.2

fig, ax = plt.subplots(figsize=(FIG_W, fig_h), dpi=120)
ax.set_xlim(0, FIG_W)
ax.set_ylim(n + 2.2, -2.6)          # inverted y: row 0 at top
ax.axis("off")
fig.patch.set_facecolor("white")


# ============================================================
# HEADER BAND
# ============================================================
ax.add_patch(plt.Rectangle((0, -2.6), FIG_W, 1.6,
                            facecolor="#1B3A5C", edgecolor="none", zorder=0))

ax.text(0.30, -1.55, "PDTS — File Structure Map",
        fontsize=22, fontweight="bold", color="white", va="center", zorder=3)
ax.text(0.30, -2.15, "templates/index.html  ·  full hierarchical layout",
        fontsize=11, color="#A8C5DC", va="center", style="italic", zorder=3)

# Metadata on the right of the header
meta_y = -1.55
ax.text(FIG_W - 0.30, meta_y, f"{lines:,} lines  ·  {size_kb:.1f} KB  ·  {modified}",
        fontsize=10, color="#A8C5DC", va="center", ha="right", zorder=3)


# ============================================================
# LEGEND (below the header)
# ============================================================
legend_items = [
    ("section", "<head>, <body>, <script>"),
    ("block",   'Container <div id="...">'),
    ("hot",     "Critical routing / safety logic"),
    ("item",    "Section or function"),
    ("leaf",    "UI element or helper"),
    ("css",     "CSS rule block"),
]

lx = 0.30
ly = -0.55
for ty, label in legend_items:
    style = TYPE_STYLE[ty]
    ax.add_patch(plt.Rectangle((lx, ly - 0.07), 0.16, 0.16,
                                facecolor=style["color"], edgecolor="none",
                                alpha=0.85, zorder=2))
    ax.text(lx + 0.26, ly, label,
            fontsize=9, color="#4a4a4a", va="center", zorder=3)
    lx += 2.35


# ============================================================
# TREE CONNECTORS
# ============================================================
GUIDE_COLOR = "#cfd8e0"
GUIDE_LW = 0.9

# For each parent, draw the vertical spine
for i, (d, _, _) in enumerate(NODES):
    child_indices = []
    for j in range(i + 1, n):
        dj = NODES[j][0]
        if dj <= d:
            break
        if dj == d + 1:
            child_indices.append(j)

    if not child_indices:
        continue

    child_depth = d + 1
    if child_depth >= len(X_GUIDE) or X_GUIDE[child_depth] is None:
        continue

    gx = X_GUIDE[child_depth]
    y_first = child_indices[0] + 0.5
    y_last  = child_indices[-1] + 0.5

    ax.plot([gx, gx], [y_first, y_last],
            color=GUIDE_COLOR, lw=GUIDE_LW, zorder=1,
            solid_capstyle="round")


# For each child node (except root), draw a horizontal tick
for i, (d, text, ty) in enumerate(NODES):
    if d == 0:
        continue
    if d >= len(X_GUIDE) or X_GUIDE[d] is None:
        continue

    y = i + 0.5
    gx = X_GUIDE[d]
    tx = X_TEXT[d]
    ax.plot([gx, tx - 0.08], [y, y],
            color=GUIDE_COLOR, lw=GUIDE_LW, zorder=1,
            solid_capstyle="round")


# ============================================================
# NODE TEXT
# ============================================================
for i, (d, text, ty) in enumerate(NODES):
    y = i + 0.5
    style = TYPE_STYLE[ty]
    tx = X_TEXT[d] if d < len(X_TEXT) else X_TEXT[-1]

    # Background chip for emphasised nodes
    if style["shape"] == "rounded":
        bbox = dict(boxstyle="round,pad=0.35",
                    facecolor=style["color"], edgecolor="none", alpha=0.10)
    elif style["shape"] == "rect":
        bbox = dict(boxstyle="square,pad=0.28",
                    facecolor=style["color"], edgecolor="none", alpha=0.08)
    else:
        bbox = None

    ax.text(tx, y, text,
            fontsize=style["size"],
            fontweight=style["weight"],
            fontstyle=style["style"],
            color=style["color"],
            va="center", ha="left", zorder=2,
            bbox=bbox)


# ============================================================
# FOOTER
# ============================================================
ax.text(0.30, n + 1.65,
        "PDTS — Kenya Police Service Front-Desk Triage Framework  ·  2026",
        fontsize=8.5, color="#a0a8b0", va="center", style="italic")
ax.text(FIG_W - 0.30, n + 1.65,
        "Samwel K. Simotwo  ·  MIT License",
        fontsize=8.5, color="#a0a8b0", va="center", ha="right", style="italic")


# ============================================================
# SAVE TO DESKTOP
# ============================================================
candidates = [
    pathlib.Path.home() / "OneDrive" / "Desktop",
    pathlib.Path.home() / "Desktop",
    pathlib.Path.cwd(),
]
DESKTOP = next((p for p in candidates if p.exists()), pathlib.Path.cwd())

png_path = DESKTOP / "PDTS_index_structure.png"
pdf_path = DESKTOP / "PDTS_index_structure.pdf"

fig.savefig(str(png_path), dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(str(pdf_path), bbox_inches="tight", facecolor="white")
plt.close(fig)


# ============================================================
# REPORT
# ============================================================
print()
print("=" * 68)
print("  PDTS File Structure Map — Generated")
print("=" * 68)
print()
if INDEX:
    print(f"  Source file : {INDEX}")
    print(f"  Lines       : {lines:,}")
    print(f"  Size        : {size_kb:.1f} KB")
    print(f"  Modified    : {modified}")
else:
    print("  Source file : not found (using placeholder metadata)")
print()
print(f"  PNG (300dpi) : {png_path}")
print(f"  PDF (vector) : {pdf_path}")
print()
print(f"  Tree nodes   : {n}")
print(f"  Figure size  : {FIG_W} × {fig_h:.1f} inches")
print()
print("  To print: open the PDF and print on A3 or A2 landscape.")
print("  To embed : drag the PNG into PowerPoint or Word.")
print()