#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""genera_proposta.py — da proposta.json a pagina web + anteprima + PDF.

Un file JSON per proposta. Un comando per generare tutto.
Nessuna dipendenza esterna obbligatoria: solo Python standard.
Chrome serve per l'anteprima (PNG) e per il PDF. 'segno' serve per il QR,
ma se manca la pagina funziona lo stesso (il QR viene saltato).

Uso:
    python generatore/genera_proposta.py proposte/demo-edilcasa
    python generatore/genera_proposta.py proposte/demo-edilcasa/proposta.json --out out
    python generatore/genera_proposta.py proposte/x/proposta.json --url-base https://esempio.pages.dev

Output (in <out>):
    <slug>/index.html      la pagina della proposta
    <slug>/og.png          anteprima 1200x630 per WhatsApp/email
    <slug>/Proposta-<Azienda>-<data>.pdf
    assets/proposta.css    fogli di stile condivisi
    assets/proposta.js
"""

import argparse
import base64
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from datetime import date
from string import Template

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT = os.path.join(ROOT, "kit")
KIT_CSS = os.path.join(KIT, "proposta.css")
KIT_JS = os.path.join(KIT, "proposta.js")
KIT_TMPL = os.path.join(KIT, "proposta.html.tmpl")
KIT_TOKENS = os.path.join(KIT, "tokens.css")
KIT_LANDING_CSS = os.path.join(KIT, "landing.css")
KIT_LANDING_TMPL = os.path.join(KIT, "landing.html.tmpl")
KIT_CONFRONTO_CSS = os.path.join(KIT, "confronto.css")

# importa config_loader
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import (  # noqa: E402
    CHROME_CANDIDATI,
    CHROME_TIMEOUT_OG,
    CHROME_TIMEOUT_PDF,
    PDF_MAX_PAGINE,
    trova_chrome,
    SITE_BASE_URL as URL_BASE_DEFAULT,
    URL_AZIENDE as URL_SITO_B2B,
)

# parole che il progetto vieta: niente marketing vuoto nei documenti
PAROLE_VIETATE = [
    "eccellenza", "eccellente", "innovativo", "rivoluzionario",
    "qualita' senza compromessi", "qualità senza compromessi", "unici nel settore",
    "passione", "amore per", "sogni", "soluzioni all'avanguardia",
]


# --------------------------------------------------------------------------
# utilita'
# --------------------------------------------------------------------------

def leggi_json(path):
    # utf-8-sig accetta sia i file con BOM (Windows, Notepad) sia quelli senza
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def fmt_prezzo(valore, decimale=False):
    """12400 -> '12.400 €' (formato italiano)."""
    if valore is None:
        return ""
    try:
        numero = float(valore)
    except (TypeError, ValueError):
        return str(valore)
    testo = ("{:,.2f}" if decimale else "{:,.0f}").format(numero)
    testo = testo.replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")
    return testo + " \u20ac"


def fmt_data(iso):
    """'2026-11-16' -> '16/11/2026'."""
    try:
        d = date.fromisoformat(iso)
    except (TypeError, ValueError):
        return iso or ""
    return "%02d/%02d/%d" % (d.day, d.month, d.year)


def slugify(testo):
    testo = (testo or "").lower()
    testo = re.sub(r"[^a-z0-9]+", "-", testo).strip("-")
    return testo or "proposta"


def versione_assets():
    """Hash breve del kit: la cartella degli asset cambia quando il kit cambia.
    Serve a non servire CSS vecchio dalla cache dei browser."""
    import hashlib
    h = hashlib.sha256()
    for percorso in (KIT_CSS, KIT_JS, KIT_TOKENS, KIT_LANDING_CSS, KIT_CONFRONTO_CSS):
        try:
            with open(percorso, "rb") as f:
                h.update(f.read())
        except OSError:
            pass
    return h.hexdigest()[:8]


def esc(testo):
    return html.escape(str(testo if testo is not None else ""), quote=True)


def trova_chrome():
    for percorso in CHROME_CANDIDATI:
        if os.path.exists(percorso):
            return percorso
    return shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chromium")


# --------------------------------------------------------------------------
# validazione
# --------------------------------------------------------------------------

def valida(d):
    """Controlla che il JSON sia completo e coerente. Restituisce lista errori."""
    errori = []

    def serve(campo, tipo=None):
        if not d.get(campo):
            errori.append("campo mancante: %s" % campo)
        elif tipo and not isinstance(d.get(campo), tipo):
            errori.append("campo %s: atteso %s" % (campo, tipo))

    serve("slug")
    serve("riferimento")
    serve("azienda", dict)
    serve("intervento")

    azienda = d.get("azienda") or {}
    for campo in ("nome",):
        if not azienda.get(campo):
            errori.append("campo mancante: azienda.%s" % campo)

    opzioni = d.get("opzioni") or []
    if len(opzioni) != 3:
        errori.append("le opzioni devono essere esattamente 3 (trovate %d)" % len(opzioni))

    ids = [o.get("id") for o in opzioni]
    if len(set(ids)) != len(ids):
        errori.append("gli id delle opzioni devono essere unici: %s" % ids)

    consigliate = [o for o in opzioni if o.get("consigliata")]
    if len(opzioni) == 3 and len(consigliate) != 1:
        errori.append("deve esserci esattamente un'opzione con \"consigliata\": true (trovate %d)" % len(consigliate))

    if len(opzioni) == 3 and consigliate:
        prezzi = []
        for o in opzioni:
            try:
                prezzi.append(float(o.get("prezzo")))
            except (TypeError, ValueError):
                prezzi.append(0.0)
        if prezzi[1] > max(prezzi):
            errori.append("l'opzione consigliata non puo' essere la piu' cara (regola del progetto)")

    for o in opzioni:
        nome = o.get("nome") or o.get("id") or "?"
        if not o.get("prezzo"):
            errori.append("opzione %s: manca il prezzo" % nome)
        if not o.get("tempi"):
            errori.append("opzione %s: manca la tempistica (regola: ogni prezzo ha i tempi)" % nome)
        if not o.get("voci"):
            errori.append("opzione %s: manca la lista delle voci incluse" % nome)
        if not o.get("perche"):
            errori.append("opzione %s: manca la riga 'perche' conviene" % nome)

    # regole di scrittura
    testo_completo = " ".join([
        d.get("intervento") or "", d.get("sintesi") or "",
        " ".join(" ".join(o.get("voci") or []) for o in opzioni),
        " ".join(o.get("perche") or "" for o in opzioni),
    ]).lower()
    for parola in PAROLE_VIETATE:
        if parola in testo_completo:
            errori.append("parola vietata nel testo: '%s' (vedi processo-consegna.md)" % parola)

    if not d.get("confronto"):
        errori.append("manca la tabella di confronto rapido")

    # ogni riga del confronto deve avere un criterio e un valore per ogni opzione
    ids_opzioni = [o.get("id") for o in opzioni]
    for n, riga in enumerate(d.get("confronto") or [], 1):
        if not riga.get("criterio"):
            errori.append("confronto riga %d: manca 'criterio'" % n)
        for oid in ids_opzioni:
            if oid not in riga:
                errori.append("confronto riga %d (%s): manca il valore per l'opzione '%s'"
                              % (n, riga.get("criterio", "?"), oid))

    return errori


# --------------------------------------------------------------------------
# link di scelta
# --------------------------------------------------------------------------

def testo_scelta(d, opzione, azienda=None):
    """Il messaggio che parte quando il committente finale sceglie.
    Se il cliente ha impostato un messaggio proprio (CTA), si usa quello."""
    azienda = azienda if azienda is not None else (d.get("azienda") or {})
    if azienda.get("cta_messaggio"):
        return azienda["cta_messaggio"]
    return (
        "Buongiorno, ho letto la proposta %s (%s).\n"
        "Voglio l'opzione %s — %s.\n"
        "Il mio nome e il mio recapito sono qui sotto."
    ) % (
        d.get("riferimento", ""),
        d.get("intervento", ""),
        opzione.get("nome", ""),
        fmt_prezzo(opzione.get("prezzo")),
    )


def link_scelta(d, opzione, azienda=None):
    """wa.me se c'e' un numero WhatsApp, altrimenti mailto.
    cta_email sovrascrive azienda.email: serve per le proposte dimostrative,
    dove il pulsante deve arrivare a noi e non all'azienda finta."""
    azienda = azienda if azienda is not None else (d.get("azienda") or {})
    testo = testo_scelta(d, opzione, azienda)
    numero = re.sub(r"\D", "", azienda.get("whatsapp") or "")
    if numero:
        return "https://wa.me/%s?text=%s" % (numero, urllib.parse.quote(testo))
    email = azienda.get("cta_email") or azienda.get("email") or ""
    if email:
        soggetto = azienda.get("cta_oggetto") or ("Scelta opzione %s — proposta %s" % (
            opzione.get("nome", ""), d.get("riferimento", "")))
        corpo = testo + "\n\n---\n" + (azienda.get("nome", ""))
        return "mailto:%s?subject=%s&body=%s" % (
            email, urllib.parse.quote(soggetto), urllib.parse.quote(corpo))
    return "#"


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def render_opzioni(d):
    out = []
    for o in d.get("opzioni") or []:
        consigliata = bool(o.get("consigliata"))
        badge = '<span class="opzione__badge">Consigliata</span>' if consigliata else ""
        iva = o.get("iva") or ""
        iva_html = " + IVA %s" % esc(iva) if iva else ""
        voci = "".join("<li>%s</li>" % esc(v) for v in (o.get("voci") or []))
        link = link_scelta(d, o)
        pulsante = (
            '<a class="btn btn--block %s" href="%s">Scelgo l\'opzione %s</a>'
            % ("btn--accent" if consigliata else "btn--ghost", esc(link), esc(o.get("nome", "")))
        )
        out.append(
            '<article class="opzione%s">%s'
            '<h3 class="opzione__nome">%s</h3>'
            '<div class="opzione__prezzo">%s<small>%s</small></div>'
            '<div class="opzione__tempi">%s</div>'
            '<ul class="opzione__voci">%s</ul>'
            '<p class="opzione__perche"><b>Perche conviene</b>%s</p>'
            '%s</article>'
            % (
                " opzione--consigliata" if consigliata else "",
                badge,
                esc(o.get("nome", "")),
                fmt_prezzo(o.get("prezzo")),
                esc(iva_html) if iva else "prezzo indicato",
                esc(o.get("tempi", "")),
                voci,
                esc(o.get("perche", "")),
                pulsante,
            )
        )
    return "\n".join(out)


def render_confronto(d):
    opzioni = d.get("opzioni") or []
    if len(opzioni) != 3:
        return ""
    intestazione = "".join('<th class="c%s">%s</th>' % (
        " evidenziata" if o.get("consigliata") else "", esc(o.get("nome", ""))) for o in opzioni)
    righe = []
    for r in d.get("confronto") or []:
        celle = ""
        for o in opzioni:
            valore = r.get(o.get("id"), "")
            if isinstance(valore, bool):
                valore = "Si" if valore else "—"
            elif valore == "":
                valore = "—"
            elif str(valore).lower() in ("no", "non incluso"):
                valore = '<span class="no">%s</span>' % esc(valore)
            elif str(valore).lower() in ("si", "sì", "incluso", "incluse"):
                valore = '<span class="si">%s</span>' % esc(valore)
            else:
                valore = esc(valore)
            celle += '<td class="c%s">%s</td>' % (" evidenziata" if o.get("consigliata") else "", valore)
        righe.append("<tr><td>%s</td>%s</tr>" % (esc(r.get("criterio", "")), celle))
    return (
        '<div class="tabella-wrap"><table class="confronto">'
        '<thead><tr><th>Cosa cambia per te</th>%s</tr></thead>'
        "<tbody>%s</tbody></table></div>"
        % (intestazione, "".join(righe))
    )


def render_lista_voci(voci, classe=""):
    if not voci:
        return ""
    return '<ul class="%s">%s</ul>' % (
        classe, "".join("<li>%s</li>" % esc(v) for v in voci))


def render_fascia_contatto(d):
    """La fascia 'parliamone'.
    Compare solo se e' una proposta dimostrativa o se il cliente ha indicato
    un indirizzo di contatto (cta_url). Su una proposta reale, privata,
    non serve: aggiungerebbe una voce che non ha senso per il committente."""
    azienda = d.get("azienda") or {}
    url = azienda.get("cta_url") or (URL_SITO_B2B + "/contatti.html" if d.get("demo") else "")
    if not url:
        return ""
    if d.get("demo"):
        titolo = "Questa e' una proposta dimostrativa"
        testo = ("Qui hai visto come funziona una proposta su tre opzioni. "
                 "Se vuoi la tua, sul tuo logo e con i tuoi prezzi, scrivici: "
                 "la prepariamo in 24-72 ore.")
    else:
        titolo = azienda.get("cta_titolo") or "Ti serve qualcosa di diverso?"
        testo = azienda.get("cta_testo") or "Scrivici: rispondiamo entro poche ore."
    return (
        '<div class="fascia-contatto">'
        '<div class="fascia-contatto__testo">'
        '<b>%s</b><p>%s</p></div>'
        '<a class="btn btn--accent" href="%s">Parliamone</a>'
        "</div>" % (esc(titolo), esc(testo), esc(url))
    )


def render_corpo(d, opts):
    azienda = d.get("azienda") or {}
    logo_html = ""
    if azienda.get("logo"):
        logo_html = '<img class="brand__logo" src="%s" alt="%s">' % (
            esc(azienda["logo"]), esc(azienda.get("nome", "")))

    # --- metadati in testata
    celle = []
    if d.get("cliente_finale", {}).get("mostra_cliente") and d["cliente_finale"].get("nome"):
        celle.append(("<span>Cliente</span><b>%s</b><small>%s</small>" % (
            esc(d["cliente_finale"]["nome"]),
            esc(d["cliente_finale"].get("indirizzo", "")))))
    if d.get("luogo"):
        celle.append("<span>Luogo lavori</span><b>%s</b>" % esc(d["luogo"]))
    if d.get("sopralluogo"):
        celle.append("<span>Sopralluogo</span><b>%s</b>" % fmt_data(d["sopralluogo"]))
    if azienda.get("referente"):
        celle.append("<span>Referente</span><b>%s</b><small>%s</small>" % (
            esc(azienda["referente"]), esc(azienda.get("telefono", ""))))
    griglia = ('<div class="doc__grid">%s</div>' % "".join(
        '<div class="doc__cell">%s</div>' % c for c in celle)) if celle else ""

    # --- corpo
    corpo = []
    corpo.append('<div class="doc">')
    corpo.append('<p class="doc__kicker">%s</p>' % esc(d.get("etichetta", "Proposta")))
    corpo.append('<h1 class="doc__title">%s</h1>' % esc(d.get("intervento", "")))
    if d.get("sintesi"):
        corpo.append('<p class="doc__lead">%s</p>' % esc(d["sintesi"]))
    corpo.append(griglia)
    corpo.append('<div class="sintesi"><h2>In sintesi</h2><p>%s</p></div>' % esc(d.get("in_sintesi", d.get("sintesi", ""))))
    corpo.append("</div>")

    # --- opzioni
    corpo.append('<section id="opzioni">')
    corpo.append('<h2 class="h2">Le tre opzioni</h2>')
    corpo.append('<div class="opzioni">%s</div>' % render_opzioni(d))
    corpo.append("</section>")

    # --- confronto
    tabella = render_confronto(d)
    if tabella:
        corpo.append('<section id="confronto">')
        corpo.append('<h2 class="h2">Confronto rapido</h2>')
        corpo.append(tabella)
        corpo.append("</section>")

    # --- compreso / non compreso
    corpo.append('<section id="dettagli">')
    corpo.append('<h2 class="h2">Dettagli, pagamenti e garanzie</h2>')
    corpo.append('<div class="colonne">')
    corpo.append('<div class="box"><h3>Cosa e\' compreso</h3>%s</div>' % render_lista_voci(d.get("compreso")))
    corpo.append('<div class="box box--no"><h3>Cosa non e\' compreso</h3>%s</div>' % render_lista_voci(d.get("escluso")))
    corpo.append('<div class="box"><h3>Pagamenti e tempi</h3>%s</div>' % render_lista_voci(d.get("pagamenti")))
    corpo.append('<div class="box"><h3>Perche scegliere noi</h3>%s</div>' % render_lista_voci(d.get("garanzie")))
    corpo.append("</div>")
    corpo.append("</section>")

    # --- chiusura
    corpo.append('<section id="conferma">')
    corpo.append('<h2 class="h2">Come confermare</h2>')
    corpo.append('<div class="chiusura">')
    corpo.append("<h3>Scegli l'opzione che preferisci</h3>")
    azienda = d.get("azienda") or {}
    canale = "WhatsApp" if re.sub(r"\D", "", azienda.get("whatsapp") or "") else "la mail"
    corpo.append("<p>Ogni opzione ha il suo pulsante <b>Scelgo l'opzione</b>: ti si apre %s "
                 "con il testo gia' pronto. Aggiungi il tuo nome e il tuo recapito, "
                 "e invia. Se preferisci, scrivi una mail a %s.</p>"
                 % (canale, esc(azienda.get("cta_email") or azienda.get("email", ""))))
    corpo.append("<p><b>Questa scelta non e' un accettazione del contratto.</b> "
                 "La proposta resta valida fino al %s. La conferma definitiva avviene con la "
                 "firma del documento.</p>" % (fmt_data(d.get("valida_fino")) if d.get("valida_fino") else "data indicata"))
    if opts.get("qr_img"):
        corpo.append('<div class="qr"><img src="%s" alt="Codice QR della proposta"><span><b>%s</b>'
                     "Apri la proposta anche dal telefono, in un secondo.</span></div>"
                     % (opts["qr_img"], esc(opts.get("url_canonica", ""))))

    contatti = []
    if azienda.get("referente"):
        contatti.append(esc(azienda["referente"]))
    if azienda.get("telefono"):
        contatti.append('<a href="tel:%s">%s</a>' % (esc(azienda["telefono"].replace(" ", "")), esc(azienda["telefono"])))
    if azienda.get("email"):
        contatti.append('<a href="mailto:%s">%s</a>' % (esc(azienda["email"]), esc(azienda["email"])))
    if contatti:
        corpo.append('<div class="contatti">%s</div>' % "".join(
            "<span>%s</span>" % c for c in contatti))
    corpo.append("</div>")

    fascia = render_fascia_contatto(d)
    if fascia:
        corpo.append("</section>")
        corpo.append('<section class="fascia-sezione no-print">%s</section>' % fascia)

    return "\n".join(corpo)


def render_barra_scelta(d):
    bottoni = []
    for o in d.get("opzioni") or []:
        classe = "accent" if o.get("consigliata") else ""
        bottoni.append('<a class="%s" href="%s">%s</a>' % (
            classe, esc(link_scelta(d, o)), esc(o.get("nome", ""))))
    return (
        '<div class="scelta-fissa no-print" aria-label="Scegli una opzione">'
        '<span class="scelta-fissa__label">Scegli</span>'
        '<div class="scelta-fissa__bottoni">%s</div>'
        "</div>" % "".join(bottoni)
    )


def render_pie(d):
    note = d.get("nota") or "Prezzi al netto di IVA. Le stime sono indicative."
    if d.get("privacy_nota"):
        note = note + " " + d["privacy_nota"]
    if d.get("demo"):
        note = ("PROPOSTA DIMOSTRATIVA. Azienda, cliente e prezzi sono inventati: "
                "il documento serve a mostrare il metodo. " + note)
    return esc(note)


# --------------------------------------------------------------------------
# pagina completa
# --------------------------------------------------------------------------

def render_pagina(d, opts):
    with open(KIT_TMPL, "r", encoding="utf-8") as f:
        tmpl = Template(f.read())

    azienda = d.get("azienda") or {}
    slug = d["slug"]
    url_canonica = opts.get("url_canonica", "")

    # colore del tema = colore del cliente
    colore = azienda.get("colori", {}).get("primario") or "#0F1729"
    brand_css = ":root{--brand:%s;--brand-ink:%s;}" % (
        colore, azienda.get("colori", {}).get("tinta") or "#F5F0E8")

    og_img = url_canonica.rstrip("/") + "/og.png"
    descrizione = d.get("meta_descrizione") or (
        "%s — proposta con tre opzioni di intervento, tempi e prezzi." % d.get("intervento", "")
    )

    piano = ""
    if opts.get("plausible"):
        piano = ('<script defer data-domain="%s" src="https://plausible.io/js/script.js"></script>'
                 % opts["plausible"])

    logo_html = ""
    if azienda.get("logo"):
        logo_html = '<img class="brand__logo" src="%s" alt="%s">' % (
            esc(azienda["logo"]), esc(azienda.get("nome", "")))

    valori = {
        "TITOLO": esc("%s — Proposta %s | %s" % (
            azienda.get("nome", "Proposta"), d.get("riferimento", ""), d.get("intervento", ""))),
        "DESCRIZIONE": esc(descrizione),
        "ROBOTS": opts.get("robots", "noindex, nofollow"),
        "COLORE_TEMA": colore,
        "URL_CANONICA": esc(url_canonica),
        "NOME_AZIENDA": esc(azienda.get("nome", "")),
        "OG_TITOLO": esc("%s — 3 opzioni | Proposta %s" % (
            azienda.get("nome", ""), d.get("riferimento", ""))),
        "OG_DESCRIZIONE": esc(descrizione),
        "OG_IMMAGINE": esc(og_img),
        "ICONA": esc((azienda.get("nome") or "P")[0].upper()),
        "BRAND_CSS": brand_css,
        "CSS_HREF": esc(opts.get("css_href", "../assets/proposta.css")),
        "JS_HREF": esc(opts.get("js_href", "../assets/proposta.js")),
        "PIANO_SCRIPT": piano,
        "LOGO": logo_html,
        "SEDE_AZIENDA": esc(azienda.get("sede", "")),
        "ETICHETTA_RIF": "Proposta",
        "RIFERIMENTO": esc(d.get("riferimento", "")),
        "CORPO": render_corpo(d, opts),
        "BARRA_SCELTA": render_barra_scelta(d),
        "NOTA_PIE": render_pie(d),
        "DATA_GENERAZIONE": fmt_data(date.today().isoformat()),
    }
    return tmpl.substitute(valori)


# --------------------------------------------------------------------------
# anteprima e PDF
# --------------------------------------------------------------------------

def genera_og(d, percorso_out, opts):
    """Scheda 1200x630 con il brand del cliente, resa da Chrome."""
    azienda = d.get("azienda") or {}
    colore = azienda.get("colori", {}).get("primario") or "#0F1729"
    accento = azienda.get("colori", {}).get("accento") or "#E8A838"

    logo = ""
    if azienda.get("logo_og") or azienda.get("logo"):
        percorso_logo = azienda.get("logo_og") or azienda.get("logo")
        logo = '<img src="%s" style="max-height:64px;background:#fff;padding:8px 14px;border-radius:8px">' % os.path.basename(percorso_logo)

    html_og = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0;padding:0}
body{width:1200px;height:630px;background:%s;color:#F5F0E8;font-family:"Segoe UI",Arial,sans-serif;
  display:flex;flex-direction:column;justify-content:space-between;padding:64px 72px;overflow:hidden;position:relative}
body::after{content:"";position:absolute;right:-140px;top:-140px;width:460px;height:460px;border-radius:50%%;background:%s;opacity:.16}
.kick{font-size:22px;letter-spacing:.18em;text-transform:uppercase;opacity:.75;font-weight:700;margin-bottom:22px}
h1{font-size:62px;line-height:1.05;font-weight:600;max-width:920px;letter-spacing:-.02em}
h2{font-size:30px;font-weight:400;opacity:.82;margin-top:22px;max-width:860px;line-height:1.3}
.foot{display:flex;justify-content:space-between;align-items:flex-end;gap:30px;position:relative}
.chip{display:inline-block;background:%s;color:#14161C;font-size:24px;font-weight:800;letter-spacing:.1em;
  text-transform:uppercase;padding:12px 26px;border-radius:100px}
.ref{font-family:Consolas,monospace;font-size:24px;opacity:.8;text-align:right}
</style></head><body>
<div><div class="kick">%s</div><h1>%s</h1><h2>%s</h2></div>
<div class="foot"><div>%s<div style="margin-top:18px">%s</div></div>
<div class="ref">Proposta %s<br>Valida fino al %s</div></div>
</body></html>""" % (
        colore, accento, accento,
        esc(d.get("etichetta", "Proposta su 3 opzioni")),
        esc(d.get("intervento", "")),
        esc("Tre livelli di intervento: il prezzo che vedi e' quello giusto per te."),
        logo,
        esc(azienda.get("nome", "")),
        esc(d.get("riferimento", "")),
        fmt_data(d.get("valida_fino")) if d.get("valida_fino") else "",
    )

    chrome = trova_chrome()
    if not chrome:
        print("  [!] Chrome non trovato: anteprima OG saltata")
        return None

    tmp_dir = tempfile.mkdtemp(prefix="og_")
    try:
        html_path = os.path.join(tmp_dir, "og.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_og)
        # il logo va copiato accanto all'html temporaneo
        if azienda.get("logo"):
            sorgente = os.path.join(opts.get("slug_dir", ""), azienda["logo"])
            if os.path.exists(sorgente):
                shutil.copy(sorgente, os.path.join(tmp_dir, os.path.basename(azienda["logo"])))

        comando = [
            chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
            "--force-device-scale-factor=1", "--virtual-time-budget=4000",
            "--window-size=1200,630", "--screenshot=%s" % percorso_out,
            "file:///" + html_path.replace("\\", "/"),
        ]
        subprocess.run(comando, capture_output=True, timeout=CHROME_TIMEOUT_OG)
        if os.path.exists(percorso_out) and os.path.getsize(percorso_out) > 1000:
            return percorso_out
        print("  [!] Anteprima OG non generata")
        return None
    except subprocess.TimeoutExpired:
        print("  [!] Timeout generazione OG (%ds)" % CHROME_TIMEOUT_OG)
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def genera_pdf(pagina_path, percorso_out):
    chrome = trova_chrome()
    if not chrome:
        print("  [!] Chrome non trovato: PDF saltato")
        return None
    comando = [
        chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", "--virtual-time-budget=5000",
        "--print-to-pdf=%s" % percorso_out,
        "file:///" + os.path.abspath(pagina_path).replace("\\", "/"),
    ]
    subprocess.run(comando, capture_output=True, timeout=CHROME_TIMEOUT_PDF)
    if os.path.exists(percorso_out) and os.path.getsize(percorso_out) > 2000:
        # Check pagina (per proposte il limite è 2, per verdetti 1)
        try:
            pdf_bytes = open(percorso_out, "rb").read()
            pagine = len(re.findall(rb"/Type\s*/Page(?![s])", pdf_bytes))
            if pagine == 0:
                m = re.search(rb"/Type\s*/Pages.{0,400}?/Count\s+(\d+)", pdf_bytes, re.S)
                if m:
                    pagine = int(m.group(1))
            # Per le proposte il target è 2 pagine, per i verdetti 1
            # Qui non sappiamo se è proposta o verdetto, quindi avvisiamo solo se > 2
            if pagine > 2:
                print("  [!] PDF ha %d pagine (attese max 2 per proposta)" % pagine)
            elif pagine == 0:
                print("  [!] PDF: impossibile contare le pagine")
        except Exception:
            pass
        return percorso_out
    print("  [!] PDF non generato")
    return None


def genera_qr(url):
    """QR in PNG base64 (data URI). Ritorna None se 'segno' non e' installato."""
    try:
        import segno
    except ImportError:
        print("  [!] 'segno' non installato: QR saltato (pip install segno)")
        return None
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "qr.png")
        segno.make(url, error="m").save(png, scale=6, border=2, dark="#0F1729", light="#FFFFFF")
        with open(png, "rb") as f:
            dati = f.read()
    return "data:image/png;base64," + base64.b64encode(dati).decode("ascii")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def pulizia_asset(out_root):
    """Le cartelle assets/<hash> si moltiplicano a ogni modifica del kit.
    Tiene solo quelle referenziate davvero da una pagina pubblicata:
    cancellare una versione ancora in uso romperebbe la pagina."""
    import re
    assets_root = os.path.join(out_root, "assets")
    if not os.path.isdir(assets_root):
        return []
    referenziate = set()
    for percorso, _, files in os.walk(out_root):
        if os.path.basename(percorso) == "assets":
            continue
        for nome in files:
            if nome != "index.html":
                continue
            try:
                with open(os.path.join(percorso, nome), "r", encoding="utf-8") as f:
                    contenuto = f.read()
            except OSError:
                continue
            for hash_ in re.findall(r"assets/([0-9a-f]{6,12})/", contenuto):
                referenziate.add(hash_)

    rimosse = []
    for voce in sorted(os.listdir(assets_root)):
        if voce == "fonts":
            continue  # cartella font self-hosted, non versionata
        percorso = os.path.join(assets_root, voce)
        if not os.path.isdir(percorso):
            continue
        if voce in referenziate:
            continue
        shutil.rmtree(percorso, ignore_errors=True)
        rimosse.append(voce)
    return rimosse


def main():
    parser = argparse.ArgumentParser(description="Genera la pagina di proposta da un JSON.")
    parser.add_argument("fonte", help="percorso della cartella o del file proposta.json")
    parser.add_argument("--out", default=ROOT, help="cartella di output (default: radice del progetto)")
    parser.add_argument("--url-base", default=URL_BASE_DEFAULT, help="base degli URL pubblici")
    parser.add_argument("--pubblico", action="store_true",
                        help="la pagina e' destinata a un sito pubblico: vieta dati personali")
    parser.add_argument("--no-pdf", action="store_true")
    parser.add_argument("--no-og", action="store_true")
    parser.add_argument("--no-qr", action="store_true")
    parser.add_argument("--plausible", default="", help="dominio Plausible per le statistiche")
    parser.add_argument("--robots", default="noindex, nofollow", help="meta robots")
    parser.add_argument("--ignora-errori", action="store_true", help="genera anche se la validazione fallisce")
    args = parser.parse_args()

    fonte = args.fonte
    if os.path.isdir(fonte):
        fonte = os.path.join(fonte, "proposta.json")
    if not os.path.exists(fonte):
        print("ERRORE: non trovo %s" % fonte)
        return 1

    d = leggi_json(fonte)

    errori = valida(d)
    if errori:
        print("VALIDAZIONE FALLITA (%d problemi):" % len(errori))
        for e in errori:
            print("  - %s" % e)
        if not args.ignora_errori:
            print("\nCorreggi il JSON e rilancia. (--ignora-errori per generare comunque)")
            return 2
        print("\nSi continua comunque (--ignora-errori).")

    slug = slugify(d.get("slug"))
    out_root = os.path.abspath(args.out)
    out_dir = os.path.join(out_root, slug)
    os.makedirs(out_dir, exist_ok=True)

    # gli asset condivisi, percorsi fissi (senza cache busting per versione)
    assets_dir = os.path.join(out_root, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    for sorgente, nome in ((KIT_CSS, "proposta.css"), (KIT_JS, "proposta.js"),
                           (KIT_TOKENS, "tokens.css"), (KIT_LANDING_CSS, "landing.css")):
        if os.path.exists(sorgente):
            shutil.copyfile(sorgente, os.path.join(assets_dir, nome))
    # copia font self-hosted (solo se sorgente e destinazione sono diverse)
    fonts_src = os.path.join(ROOT, "assets", "fonts")
    fonts_dst = os.path.join(assets_dir, "fonts")
    if os.path.isdir(fonts_src) and os.path.abspath(fonts_src) != os.path.abspath(fonts_dst):
        if os.path.exists(fonts_dst):
            shutil.rmtree(fonts_dst)
        os.makedirs(fonts_dst, exist_ok=True)
        for entry in os.listdir(fonts_src):
            shutil.copy2(os.path.join(fonts_src, entry), os.path.join(fonts_dst, entry))

    url_canonica = "%s/%s/" % (args.url_base.rstrip("/"), slug)
    opts = {
        "url_canonica": url_canonica,
        "css_href": "../assets/proposta.css",
        "js_href": "../assets/proposta.js",
        "robots": args.robots,
        "plausible": args.plausible,
        "assets_root": out_root,
        "slug_dir": out_dir,
    }

    # immagini del cliente (logo e foto): si copiano dentro la cartella della proposta
    img_src = os.path.join(os.path.dirname(os.path.abspath(fonte)), "images")
    if os.path.isdir(img_src):
        img_dst = os.path.join(out_dir, "images")
        if os.path.isdir(img_dst):
            shutil.rmtree(img_dst)
        shutil.copytree(img_src, img_dst)

    # QR
    if not args.no_qr:
        qr = genera_qr(url_canonica)
        if qr:
            opts["qr_img"] = qr

    # pagina
    pagina = render_pagina(d, opts)
    pagina_path = os.path.join(out_dir, "index.html")
    with open(pagina_path, "w", encoding="utf-8") as f:
        f.write(pagina)

    # controllo privacy: dati personali in una pagina destinata al pubblico
    cliente = d.get("cliente_finale") or {}
    if args.pubblico and cliente.get("nome") and not cliente.get("mostra_cliente"):
        print("  [i] Dati del committente finale esclusi dalla pagina (privacy): %s" % cliente["nome"])

    risultati = [pagina_path]

    # anteprima OG
    if not args.no_og:
        og_path = os.path.join(out_dir, "og.png")
        if genera_og(d, og_path, opts):
            risultati.append(og_path)

    # PDF
    if not args.no_pdf:
        nome_pdf = "Proposta-%s-%s.pdf" % (
            slugify(d.get("azienda", {}).get("nome", "cliente")),
            (d.get("riferimento") or "").replace("/", "-"))
        pdf_path = os.path.join(out_dir, nome_pdf)
        if genera_pdf(pagina_path, pdf_path):
            risultati.append(pdf_path)

    print("\nGenerato per '%s':" % d.get("slug"))
    for p in risultati:
        print("  %s" % os.path.relpath(p, out_root))
    print("URL: %s" % url_canonica)
    rimosse = pulizia_asset(out_root)
    if rimosse:
        print("Asset versione precedente rimossa: %s" % ", ".join(rimosse))
    return 0


if __name__ == "__main__":
    sys.exit(main())
