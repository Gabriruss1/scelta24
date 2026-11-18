#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analizza.py — genera un report di confronto preventivi da analisi.json.

Produce: <slug>/index.html, verdetto.pdf (1 pagina), og.png, domande.md.
Zero dipendenze obbligatorie: Python standard. Chrome per og/pdf.

Uso:
  python generatore/analizza.py analisi/confronto-demo-bagno
  python generatore/analizza.py analisi/x/analisi.json --out out
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from string import Template

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, "kit")
KIT_TMPL = os.path.join(KIT, "confronto.html.tmpl")
KIT_CSS = os.path.join(KIT, "confronto.css")
KIT_TOKENS = os.path.join(KIT, "tokens.css")

URL_BASE_DEFAULT = "https://gabriruss1.github.io/scelta24"
URL_AZIENDE = "https://gabriruss1.github.io/preventivi24"
URL_CONTATTO = "/contatti.html?servizio=confronto"
URL_ANALISI_COMPLETA = "/contatti.html?servizio=analisi-completa"

# importa utility dal generatore esistente
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from genera_proposta import (  # noqa: E402
    esc, fmt_prezzo, trova_chrome, versione_assets, pulizia_asset,
)


def carica_json(percorso):
    with open(percorso, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def valida(d):
    errori = []
    for campo in ("slug", "titolo", "intervento", "preventivi", "verdetto"):
        if not d.get(campo):
            errori.append("campo mancante: %s" % campo)
    preventivi = d.get("preventivi") or []
    if len(preventivi) < 2:
        errori.append("servono almeno 2 preventivi (trovati %d)" % len(preventivi))
    ids = [p.get("id") for p in preventivi]
    if len(set(ids)) != len(ids):
        errori.append("gli id dei preventivi devono essere unici: %s" % ids)
    for p in preventivi:
        pid = p.get("id") or "?"
        if not p.get("azienda"):
            errori.append("preventivo %s: manca azienda" % pid)
        if p.get("prezzo_dichiarato") in (None, ""):
            errori.append("preventivo %s: manca prezzo_dichiarato" % pid)
        if p.get("costo_reale") in (None, ""):
            errori.append("preventivo %s: manca costo_reale" % pid)
    v = d.get("verdetto") or {}
    if not v.get("scelta"):
        errori.append("verdetto: manca 'scelta'")
    elif v.get("scelta") not in ids:
        errori.append("verdetto.scelta '%s' non corrisponde a nessun preventivo %s" % (v.get("scelta"), ids))
    if not v.get("perche"):
        errori.append("verdetto: manca 'perche'")
    livello = d.get("livello")
    if livello and livello not in ("gratuito", "completo"):
        errori.append("livello non valido: '%s' (usa 'gratuito' o 'completo')" % livello)
    return errori


def fmt_eur(valore):
    try:
        return fmt_prezzo(float(valore))
    except (TypeError, ValueError):
        return esc(valore)


def lista_ul(voci):
    voci = [v for v in (voci or []) if v]
    if not voci:
        return "<p style='color:var(--grey);margin:0'>Nessuna</p>"
    return "<ul>" + "".join("<li>%s</li>" % esc(v) for v in voci) + "</ul>"


def render_verdetto(d):
    v = d.get("verdetto") or {}
    scelta = v.get("scelta")
    # trova preventivo scelto per nome
    nome_scelto = scelta
    for p in d.get("preventivi") or []:
        if p.get("id") == scelta:
            nome_scelto = p.get("azienda") or scelta
            break
    numeri = []
    if v.get("costo_reale_scelto") is not None:
        numeri.append('<div class="pill"><small>Costo reale scelto</small><strong>%s</strong></div>' % fmt_eur(v.get("costo_reale_scelto")))
    if v.get("costo_reale_altro") is not None:
        numeri.append('<div class="pill"><small>Costo reale alternativa</small><strong>%s</strong></div>' % fmt_eur(v.get("costo_reale_altro")))
    if v.get("risparmio"):
        numeri.append('<div class="pill"><small>Risparmio/rischio evitato</small><strong>%s</strong></div>' % esc(v.get("risparmio")))
    punti = "".join("<li>%s</li>" % esc(x) for x in (v.get("punti") or []))
    return (
        '<section class="verdetto" id="verdetto">'
        '<p class="verdetto__kicker">Verdetto</p>'
        '<h2>%s</h2>'
        '<p class="verdetto__perche">%s</p>'
        '<div class="verdetto__numeri">%s</div>'
        '%s'
        '</section>'
    ) % (
        esc(v.get("titolo") or ("Scegli %s" % nome_scelto)),
        esc(v.get("perche", "")),
        "".join(numeri),
        ("<ul>%s</ul>" % punti) if punti else "",
    )


def render_tabella(d):
    preventivi = d.get("preventivi") or []
    scelta = (d.get("verdetto") or {}).get("scelta")
    ids = [p.get("id") for p in preventivi]
    head = "<tr><th>Criterio</th>" + "".join(
        '<th class="%s">%s <small style="display:block;font-weight:500;opacity:.7">(%s)</small></th>' % (
            "win" if p.get("id") == scelta else "",
            esc(p.get("azienda", "")), esc(p.get("id", ""))
        ) for p in preventivi
    ) + "</tr>"

    def riga(label, valori, clsfn=None):
        celle = ""
        for i, val in enumerate(valori):
            cls = clsfn(i, val) if clsfn else ""
            celle += '<td class="%s">%s</td>' % (cls, val)
        return "<tr><th>%s</th>%s</tr>" % (esc(label), celle)

    def cls_scelta(i, _):
        return "win" if ids[i] == scelta else ""

    def costo_cls(i, _):
        base = "costo " + ("win" if ids[i] == scelta else "")
        return base

    rows = []
    rows.append(riga("Prezzo dichiarato", [fmt_eur(p.get("prezzo_dichiarato")) for p in preventivi], cls_scelta))
    rows.append(riga("IVA", [esc(p.get("iva") or "Non indicata") for p in preventivi], cls_scelta))
    rows.append(riga("Costo reale stimato", [fmt_eur(p.get("costo_reale")) for p in preventivi], costo_cls))
    rows.append(riga("Caparra / pagamenti", [esc(p.get("caparra") or "Non indicato") for p in preventivi], cls_scelta))
    rows.append(riga("Tempi", [esc(p.get("tempi") or "Non indicati") for p in preventivi], cls_scelta))
    rows.append(riga("Garanzia", [esc(p.get("garanzia") or "Non indicata") for p in preventivi], cls_scelta))
    rows.append(riga("Voci incluse", [lista_ul(p.get("voci_incluse")) for p in preventivi], cls_scelta))

    def mancanti_cell(p):
        manc = p.get("voci_mancanti") or []
        if not manc:
            return "<p style='color:#16a34a;margin:0;font-weight:600'>Nessuna voce critica mancante</p>"
        return '<ul class="missing">' + "".join("<li>%s</li>" % esc(v) for v in manc) + "</ul>"

    rows.append(riga("Voci mancanti / escluse", [mancanti_cell(p) for p in preventivi], cls_scelta))
    rows.append(riga("Note", [esc(p.get("note") or "-") for p in preventivi], cls_scelta))

    return (
        '<div class="tabella-wrap"><table class="confronto-tbl">'
        '<thead>%s</thead><tbody>%s</tbody></table></div>'
    ) % (head, "".join(rows))


def render_semafori(d):
    sem = d.get("semafori") or []
    if not sem:
        return ""
    carte = []
    for s in sem:
        livello = (s.get("livello") or "giallo").lower()
        if livello not in ("rosso", "giallo", "verde"):
            livello = "giallo"
        carte.append(
            '<div class="semaforo semaforo--%s">'
            '<div class="semaforo__head"><span class="dot"></span><h3>%s</h3></div>'
            '<p>%s</p></div>'
        % (livello, esc(s.get("criterio", "")), esc(s.get("testo", ""))))
    return '<div class="semafori">%s</div>' % "".join(carte)


def render_domande(d):
    dom = d.get("domande") or []
    if not dom:
        return ""
    items = []
    for q in dom:
        az = q.get("azienda") or ""
        pref = ("<b>Da chiedere a %s</b>" % esc(az)) if az else ""
        items.append("<li>%s%s</li>" % (pref, esc(q.get("domanda", ""))))
    return '<ul class="domande">%s</ul>' % "".join(items)


def render_corpo(d):
    preventivi = d.get("preventivi") or []
    nomi = ", ".join(p.get("azienda", "?") for p in preventivi)
    meta = []
    if d.get("intervento"):
        meta.append("<span><b>Intervento:</b> %s</span>" % esc(d.get("intervento")))
    if d.get("luogo"):
        meta.append("<span><b>Luogo:</b> %s</span>" % esc(d.get("luogo")))
    if d.get("data"):
        meta.append("<span><b>Data analisi:</b> %s</span>" % esc(d.get("data")))
    if d.get("riferimento"):
        meta.append("<span><b>Riferimento:</b> %s</span>" % esc(d.get("riferimento")))

    demo_badge = '<span class="badge-demo">Confronto dimostrativo</span>' if d.get("demo") else ""
    livello = d.get("livello") or "gratuito"
    if livello == "completo":
        livello_badge = '<span class="badge-livello badge--completa">Analisi completa</span>'
    else:
        livello_badge = '<span class="badge-livello badge--gratuito">Analisi gratuita</span>'

    parti = []
    parti.append(
        '<section class="hero hero--confronto"><div class="wrap">'
        '%s%s'
        '<p class="hero__kicker">Confronto preventivi</p>'
        '<h1>%s</h1>'
        '<p class="hero__lead">Abbiamo messo a confronto %s sullo stesso lavoro. '
        'Qui sotto trovi il costo reale, le voci mancanti, i rischi e il verdetto.</p>'
        '<div class="meta-riga">%s</div>'
        '</div></section>'
        % (demo_badge, livello_badge, esc(d.get("titolo", "Confronto preventivi")), esc(nomi), "".join(meta))
    )

    parti.append('<section class="sezione"><div class="wrap">%s</div></section>' % render_verdetto(d))

    if livello == "completo":
        parti.append(
            '<section class="sezione"><div class="wrap">'
            '<h2 class="h2">I numeri senza trucchi</h2>'
            '<p class="sottotitolo">Prezzo dichiarato, IVA, costo reale stimato e cosa e\' davvero incluso. Riga per riga.</p>'
            '%s</div></section>' % render_tabella(d)
        )

        sem = render_semafori(d)
        if sem:
            parti.append(
                '<section class="sezione sezione--scura"><div class="wrap">'
                '<h2 class="h2">Rischi e segnali</h2>'
                '<p class="sottotitolo">Clausole, omissioni e punti da chiarire prima di firmare.</p>'
                '%s</div></section>' % sem
            )

        dom = render_domande(d)
        if dom:
            parti.append(
                '<section class="sezione"><div class="wrap">'
                '<h2 class="h2">Le domande da fare alle aziende</h2>'
                '<p class="sottotitolo">Copiale e inviale: le risposte scritte contano piu\' delle parole al telefono.</p>'
                '%s</div></section>' % dom
            )
    else:
        parti.append(
            '<section class="sezione"><div class="wrap">'
            '<div class="upsell"><h2 class="h2">Vuoi l\'analisi completa?</h2>'
            '<p>Questo report gratuito ti dice quale preventivo scegliere e perch&eacute;. '
            'L\'analisi completa (39 &euro;) aggiunge: tabella riga per riga con voci mancanti e costo reale, '
            'semafori di rischio su caparra, garanzia e tempi, e le domande scritte da inviare alle aziende. '
            'I documenti non addestrano modelli e vengono eliminati dopo la consegna.</p>'
            '<div class="hero__azioni" style="justify-content:center; margin-top: var(--s-4);">'
            '<a class="btn btn--accent" href="%s">Richiedi l\'analisi completa</a>'
            '</div></div></div></section>' % URL_ANALISI_COMPLETA
        )

    if d.get("metodo"):
        parti.append(
            '<section class="sezione"><div class="wrap">'
            '<h2 class="h2">Metodo e limiti</h2>'
            '<div class="metodo"><p>%s</p></div></div></section>' % esc(d.get("metodo"))
        )

    if livello == "completo":
        parti.append(
            '<section class="sezione no-print"><div class="wrap">'
            '<div class="cta-blocco"><h2>Hai altri preventivi sul tavolo?</h2>'
            '<p>Mandaci i PDF: li confrontiamo riga per riga e ti diamo un verdetto chiaro, con le domande da fare. '
            'Gratis, controllato da una persona prima di arrivarti. I documenti non addestrano modelli e vengono eliminati dopo la consegna.</p>'
            '<div class="hero__azioni" style="justify-content:center">'
            '<a class="btn btn--accent" href="%s">Invia i tuoi preventivi</a>'
            '<a class="btn btn--ghost" href="%s">Sei un\'azienda? Preventivi24</a>'
            '</div></div></div></section>' % (URL_CONTATTO, URL_AZIENDE)
        )

    return "\n".join(parti)


def render_domande_md(d):
    righe = ["# Domande da fare alle aziende", "",
             "Confronto: %s" % d.get("titolo", ""), ""]
    for q in d.get("domande") or []:
        az = q.get("azienda") or ""
        pref = ("**A %s:** " % az) if az else "- "
        righe.append("- %s%s" % (pref if not az else pref, q.get("domanda", "")))
    if not d.get("domande"):
        righe.append("- Nessuna domanda specifica: chiedi conferma scritta di prezzi, tempi e garanzie.")
    righe += ["", "Inviale per iscritto e conserva le risposte."]
    return "\n".join(righe) + "\n"


def genera_og(d, percorso_out):
    v = d.get("verdetto") or {}
    titolo = v.get("titolo") or d.get("titolo") or "Confronto preventivi"
    sottotitolo = (v.get("perche") or "")[:140]
    html_og = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0;padding:0}
body{width:1200px;height:630px;background:#0F1729;color:#F5F0E8;font-family:"Segoe UI",Arial,sans-serif;
  display:flex;flex-direction:column;justify-content:space-between;padding:64px 72px;overflow:hidden;position:relative}
body::after{content:"";position:absolute;right:-140px;top:-140px;width:460px;height:460px;border-radius:50%%;background:#E8A838;opacity:.16}
.kick{font-size:22px;letter-spacing:.18em;text-transform:uppercase;opacity:.75;font-weight:700;margin-bottom:22px;color:#E8A838}
h1{font-size:58px;line-height:1.08;font-weight:600;max-width:980px;letter-spacing:-.02em}
h2{font-size:28px;font-weight:400;opacity:.85;margin-top:22px;max-width:900px;line-height:1.35}
.foot{font-size:24px;opacity:.7}
</style></head><body>
<div><div class="kick">Scelta24 · Confronto preventivi</div><h1>%s</h1><h2>%s</h2></div>
<div class="foot">Costo reale, rischi e verdetto. Gratis, controllato da una persona.</div>
</body></html>""" % (esc(titolo), esc(sottotitolo))

    chrome = trova_chrome()
    if not chrome:
        print("  [!] Chrome non trovato: og.png saltato")
        return None
    tmp_dir = tempfile.mkdtemp(prefix="ogc_")
    try:
        html_path = os.path.join(tmp_dir, "og.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_og)
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
               "--force-device-scale-factor=1", "--virtual-time-budget=4000",
               "--window-size=1200,630", "--screenshot=%s" % percorso_out,
               "file:///" + html_path.replace("\\", "/")]
        subprocess.run(cmd, capture_output=True, timeout=90)
        if os.path.exists(percorso_out) and os.path.getsize(percorso_out) > 1000:
            return percorso_out
        print("  [!] og.png non generato")
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def genera_pdf_verdetto(d, percorso_out):
    v = d.get("verdetto") or {}
    preventivi = d.get("preventivi") or []
    scelta = v.get("scelta")
    nome_scelto = scelta
    for p in preventivi:
        if p.get("id") == scelta:
            nome_scelto = p.get("azienda") or scelta
    punti = "".join("<li>%s</li>" % esc(x) for x in (v.get("punti") or [])[:5])
    righe = []
    for p in preventivi:
        cls = "win" if p.get("id") == scelta else ""
        righe.append("<tr class='%s'><td>%s</td><td>%s</td><td class='c'>%s</td><td>%s</td></tr>" % (
            cls, esc(p.get("azienda", "")), fmt_eur(p.get("prezzo_dichiarato")),
            fmt_eur(p.get("costo_reale")), esc(p.get("garanzia") or "-"),
        ))
    dom = "".join("<li><b>%s:</b> %s</li>" % (esc(q.get("azienda", "")), esc(q.get("domanda", "")))
                  for q in (d.get("domande") or [])[:4])

    html_pdf = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@page{size:A4;margin:16mm}
*{box-sizing:border-box}
body{font-family:"Segoe UI",Arial,sans-serif;color:#111827;font-size:11pt;line-height:1.45;margin:0}
.kick{font-size:9pt;letter-spacing:.14em;text-transform:uppercase;color:#B45309;font-weight:700;margin-bottom:6px}
h1{font-size:20pt;line-height:1.15;margin:0 0 8px;color:#0F1729}
.lead{font-size:11.5pt;color:#374151;margin:0 0 14px}
.box{background:#0F1729;color:#F5F0E8;border-radius:10px;padding:14px 16px;margin:12px 0}
.box h2{margin:0 0 6px;font-size:14pt}
.box p{margin:0;opacity:.92}
ul{margin:8px 0 0 18px;padding:0} li{margin-bottom:4px}
table{width:100%%;border-collapse:collapse;margin-top:10px;font-size:10pt}
th,td{border:1px solid #E5E7EB;padding:8px 10px;text-align:left;vertical-align:top}
thead th{background:#F5F0E8;font-size:8.5pt;letter-spacing:.08em;text-transform:uppercase;color:#374151}
.c{font-weight:700;font-family:Consolas,monospace}
.win td{background:#ECFDF5}
h3{font-size:11pt;margin:14px 0 6px;color:#0F1729}
.foot{margin-top:14px;font-size:8.5pt;color:#6B7280;border-top:1px solid #E5E7EB;padding-top:8px}
</style></head><body>
<div class="kick">Scelta24 · Confronto preventivi</div>
<h1>%s</h1>
<p class="lead">%s</p>
<div class="box"><h2>Verdetto: scegli %s</h2><p>%s</p>%s</div>
<table><thead><tr><th>Preventivo</th><th>Prezzo dichiarato</th><th>Costo reale stimato</th><th>Garanzia</th></tr></thead>
<tbody>%s</tbody></table>
%s
<div class="foot">Analisi dimostrativa/assistita: controllata prima dell'invio. I costi reali sono stime basate sulle voci dichiarate e sulle omissioni indicate. Scelta24, un servizio Preventivi24.</div>
</body></html>""" % (
        esc(d.get("titolo", "Confronto preventivi")),
        esc(d.get("intervento", "")),
        esc(nome_scelto),
        esc(v.get("perche", "")),
        ("<ul>%s</ul>" % punti) if punti else "",
        "".join(righe),
        ("<h3>Domande da fare</h3><ul>%s</ul>" % dom) if dom else "",
    )

    chrome = trova_chrome()
    if not chrome:
        print("  [!] Chrome non trovato: verdetto.pdf saltato")
        return None
    tmp_dir = tempfile.mkdtemp(prefix="vpdf_")
    try:
        html_path = os.path.join(tmp_dir, "verdetto.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_pdf)
        cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
               "--no-pdf-header-footer", "--virtual-time-budget=5000",
               "--print-to-pdf=%s" % percorso_out,
               "file:///" + html_path.replace("\\", "/")]
        subprocess.run(cmd, capture_output=True, timeout=120)
        if os.path.exists(percorso_out) and os.path.getsize(percorso_out) > 1000:
            return percorso_out
        print("  [!] verdetto.pdf non generato")
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Genera un report di confronto da analisi.json")
    ap.add_argument("input", help="cartella analisi o file analisi.json")
    ap.add_argument("--out", default=ROOT, help="cartella di destinazione (default: root progetto)")
    ap.add_argument("--url-base", default=URL_BASE_DEFAULT)
    ap.add_argument("--no-og", action="store_true")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--ignora-errori", action="store_true")
    args = ap.parse_args()

    percorso = os.path.abspath(args.input)
    if os.path.isdir(percorso):
        json_path = os.path.join(percorso, "analisi.json")
    else:
        json_path = percorso
        percorso = os.path.dirname(percorso)
    if not os.path.exists(json_path):
        print("Non trovo %s" % json_path)
        return 1

    d = carica_json(json_path)
    errori = valida(d)
    if errori and not args.ignora_errori:
        print("VALIDAZIONE FALLITA (%d problemi):" % len(errori))
        for e in errori:
            print("  - %s" % e)
        return 1
    if errori:
        print("AVVISO: %d problemi ignorati" % len(errori))

    slug = d.get("slug") or os.path.basename(percorso)
    out_root = os.path.abspath(args.out)
    out_dir = os.path.join(out_root, slug)
    os.makedirs(out_dir, exist_ok=True)

    # asset
    ver = versione_assets()
    assets_dir = os.path.join(out_root, "assets", ver)
    os.makedirs(assets_dir, exist_ok=True)
    for sorg, nome in ((KIT_CSS, "confronto.css"), (KIT_TOKENS, "tokens.css"),
                       (os.path.join(KIT, "landing.css"), "landing.css")):
        if os.path.exists(sorg):
            shutil.copyfile(sorg, os.path.join(assets_dir, nome))

    url_base = args.url_base.rstrip("/")
    url_canon = "%s/%s/" % (url_base, slug)
    robots = "index, follow" if d.get("demo") else "noindex, nofollow"
    descr = d.get("descrizione") or ("Confronto tra %d preventivi per %s: costo reale, rischi e verdetto." % (len(d.get("preventivi") or []), d.get("intervento", "")))

    with open(KIT_TMPL, "r", encoding="utf-8") as f:
        tmpl = Template(f.read())

    nota_pie = ("Confronto dimostrativo con dati di esempio." if d.get("demo")
                else "Analisi riservata a chi ha ricevuto il link.")

    html_out = tmpl.substitute({
        "TITOLO": esc(d.get("titolo", "Confronto preventivi") + " | Scelta24"),
        "DESCRIZIONE": esc(descr),
        "ROBOTS": esc(robots),
        "URL_CANONICA": esc(url_canon),
        "OG_TITOLO": esc((d.get("verdetto") or {}).get("titolo") or d.get("titolo", "")),
        "OG_DESCRIZIONE": esc((d.get("verdetto") or {}).get("perche") or descr),
        "OG_IMMAGINE": esc(url_canon + "og.png"),
        "CSS_HREF": esc("../assets/%s/confronto.css" % ver),
        "PIANO_SCRIPT": "",
        "CORPO": render_corpo(d),
        "URL_CONTATTO": esc(URL_CONTATTO),
        "URL_AZIENDE": esc(URL_AZIENDE),
        "NOTA_PIE": nota_pie,
    })

    out_index = os.path.join(out_dir, "index.html")
    with open(out_index, "w", encoding="utf-8") as f:
        f.write(html_out)

    with open(os.path.join(out_dir, "domande.md"), "w", encoding="utf-8") as f:
        f.write(render_domande_md(d))

    if not args.no_og:
        genera_og(d, os.path.join(out_dir, "og.png"))
    if not args.no_pdf:
        genera_pdf_verdetto(d, os.path.join(out_dir, "verdetto.pdf"))

    print("Confronto generato: %s" % out_dir)
    print("  index.html  domande.md  %s  %s" % (
        "og.png" if not args.no_og else "-",
        "verdetto.pdf" if not args.no_pdf else "-",
    ))
    print("URL: %s" % url_canon)
    return 0


if __name__ == "__main__":
    sys.exit(main())
