#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_site.py — costruisce la parte pubblica del sito.

Genera:
    index.html      la landing (il metodo del preventivo a 3 opzioni)
    robots.txt
    sitemap.xml     solo le pagine indicizzabili
    images/og.png   anteprima della landing

Le pagine di proposta non le tocca: le genera genera_proposta.py.
Nella sitemap finiscono solo le pagine con robots "index": le proposte
reali (noindex) restano fuori.

Uso:
    python generatore/build_site.py --url-base https://gabriruss1.github.io/preventivi24-clienti
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
KIT_LANDING_CSS = os.path.join(KIT, "landing.css")
KIT_LANDING_TMPL = os.path.join(KIT, "landing.html.tmpl")
KIT_TOKENS = os.path.join(KIT, "tokens.css")

URL_AZIENDE = "https://gabriruss1.github.io/preventivi24"

FAQ = [
    ("Perche' un preventivo con un solo prezzo perde lavori?",
     "Perche' il cliente non ha niente da confrontare: mette il tuo totale accanto a quello "
     "del concorrente e vince chi costa meno. Con tre livelli dello stesso lavoro confronta "
     "il valore, e il prezzo torna a essere una variabile fra le altre."),
    ("La fascia consigliata deve essere la piu' cara?",
     "No, e non deve esserlo. E' quella che risolve il problema con il rapporto migliore tra "
     "valore e prezzo. Il metodo prevede di scriverlo per iscritto in una riga: se la riga "
     "non convince, la fascia e' sbagliata."),
    ("Cambia il lavoro che faccio?",
     "No. Cambia solo la presentazione. Il sopralluogo, il listino, i materiali e la "
     "esecuzione restano tuoi. I tre livelli si ricavano da quello che gia' vendi, non "
     "da un listario inventato."),
    ("Che cosa riceve il cliente finale?",
     "Una proposta che si apre dal telefono o dal computer: tre opzioni con prezzo, tempi e "
     "voci incluse, una tabella di confronto e la sua scelta in un tocco. Resta valida "
     "fino alla data indicata."),
    ("I miei prezzi restano riservati?",
     "Le proposte reali non sono indicizzate e non finiscono in nessun elenco pubblico: "
     "si aprono solo con il link che ricevi. Gli esempi pubblici di questo sito usano dati "
     "dimostrativi."),
]


def esc(testo):
    return html.escape(str(testo if testo is not None else ""), quote=True)


def fmt_prezzo(valore):
    try:
        numero = float(valore)
    except (TypeError, ValueError):
        return ""
    testo = "{:,.0f}".format(numero).replace(",", "\u00a0").replace(".", ",").replace("\u00a0", ".")
    return testo + " \u20ac"


def cerca_proposte(out_root):
    """Le proposte gia' generate: cartelle con index.html dentro out_root."""
    trovate = []
    for nome in sorted(os.listdir(out_root)):
        percorso = os.path.join(out_root, nome)
        if not os.path.isdir(percorso) or nome.startswith("."):
            continue
        indice = os.path.join(percorso, "index.html")
        if not os.path.exists(indice):
            continue
        with open(indice, "r", encoding="utf-8") as f:
            contenuto = f.read()
        robots = "noindex"
        m = re.search(r'<meta name="robots" content="([^"]+)"', contenuto)
        if m:
            robots = m.group(1)
        titolo = ""
        m = re.search(r"<title>(.*?)</title>", contenuto, re.S)
        if m:
            titolo = m.group(1).strip()
        trovate.append({
            "slug": nome,
            "robots": robots,
            "titolo": titolo,
            "indicizzabile": "index" in robots,
            "og": os.path.join(percorso, "og.png"),
        })
    return trovate


def costruisci_carte(proposte):
    carte = []
    for p in proposte:
        if not p["indicizzabile"]:
            continue
        img = ("<img class=\"esempio__img\" src=\"%s/og.png\" alt=\"Anteprima della proposta %s\" loading=\"lazy\">"
               % (esc(p["slug"]), esc(p["slug"])))
        carte.append(
            '<a class="esempio" href="%s/index.html">%s'
            '<div class="esempio__corpo"><span>Esempio reale</span>'
            "<h3>%s</h3><p>Si apre su telefono, con le tre opzioni affiancate.</p></div></a>"
            % (esc(p["slug"]), img, esc(p["titolo"]))
        )
    if not carte:
        carte.append('<p class="sottotitolo">Gli esempi sono in preparazione.</p>')
    return "\n".join(carte)


def costruisci_faq():
    blocchi = []
    for domanda, risposta in FAQ:
        blocchi.append(
            "<details><summary>%s</summary><p>%s</p></details>" % (esc(domanda), esc(risposta))
        )
    return "\n".join(blocchi)


def genera_og_landing(percorso_out):
    """Scheda 1200x630 della landing."""
    chrome_candidati = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        shutil.which("chrome") or shutil.which("google-chrome"),
    ]
    chrome = next((c for c in chrome_candidati if c and os.path.exists(c)), None)
    if not chrome:
        print("  [!] Chrome non trovato: anteprima OG saltata")
        return None

    html_og = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{box-sizing:border-box;margin:0;padding:0}
body{width:1200px;height:630px;background:#0F1729;color:#F5F0E8;font-family:"Segoe UI",Arial,sans-serif;
  display:flex;flex-direction:column;justify-content:space-between;padding:70px 72px;overflow:hidden;position:relative}
body::after{content:"";position:absolute;right:-120px;bottom:-160px;width:520px;height:520px;border-radius:50%;background:#E8A838;opacity:.14}
.kick{font-size:24px;letter-spacing:.18em;text-transform:uppercase;color:#E8A838;font-weight:700;margin-bottom:24px}
h1{font-size:68px;line-height:1.04;font-weight:600;letter-spacing:-.02em;max-width:940px}
h1 em{font-style:normal;color:#E8A838}
h2{font-size:30px;font-weight:400;opacity:.8;margin-top:26px;max-width:820px;line-height:1.35}
.foot{font-size:24px;opacity:.6;position:relative;letter-spacing:.04em}
</style></head><body>
<div><div class="kick">Il metodo del preventivo a 3 opzioni</div>
<h1>Un preventivo, tre livelli. Il cliente sceglie il <em>valore</em>.</h1>
<h2>Base, Consigliata e Completa: prezzi, tempi e cosa e' incluso. Con la fascia consigliata in evidenza.</h2></div>
<div class="foot">Preventivi24 &middot; proposte su tre opzioni per aziende e committenti finali</div>
</body></html>"""

    with tempfile.TemporaryDirectory() as tmp:
        html_path = os.path.join(tmp, "og.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_og)
        comando = [
            chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
            "--force-device-scale-factor=1", "--virtual-time-budget=4000",
            "--window-size=1200,630", "--screenshot=%s" % percorso_out,
            "file:///" + html_path.replace("\\", "/"),
        ]
        subprocess.run(comando, capture_output=True, timeout=90)
    if os.path.exists(percorso_out) and os.path.getsize(percorso_out) > 1000:
        return percorso_out
    print("  [!] Anteprima OG della landing non generata")
    return None


def costruisci_jsonld(url_base):
    """Dati strutturati: le domande frequenti e il sito.
    E' cio' che permette a Google di mostrare le risposte sotto il risultato."""
    faq = [{
        "@type": "Question",
        "name": domanda,
        "acceptedAnswer": {"@type": "Answer", "text": risposta},
    } for domanda, risposta in FAQ]
    dati = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": "Preventivi24",
                "url": url_base + "/",
                "inLanguage": "it-IT",
                "description": "Il metodo del preventivo a 3 opzioni: Base, Consigliata, Completa.",
            },
            {
                "@type": "FAQPage",
                "mainEntity": faq,
            },
        ],
    }
    return json.dumps(dati, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Costruisce la parte pubblica del sito.")
    parser.add_argument("--out", default=ROOT, help="cartella del sito")
    parser.add_argument("--url-base", default="https://gabriruss1.github.io/preventivi24-clienti")
    parser.add_argument("--plausible", default="", help="dominio Plausible")
    args = parser.parse_args()

    out_root = os.path.abspath(args.out)
    url_base = args.url_base.rstrip("/")

    proposte = cerca_proposte(out_root)
    indicizzabili = [p for p in proposte if p["indicizzabile"]]

    # --- landing
    with open(KIT_LANDING_TMPL, "r", encoding="utf-8") as f:
        tmpl = Template(f.read())

    # stessa versione degli asset usata dal generatore di proposte
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from genera_proposta import versione_assets, pulizia_asset
    versione = versione_assets()

    # gli asset devono esistere: se il generatore non e' mai girato, si copiano
    assets_dir = os.path.join(out_root, "assets", versione)
    os.makedirs(assets_dir, exist_ok=True)
    for sorgente, nome in ((os.path.join(KIT, "proposta.css"), "proposta.css"),
                           (os.path.join(KIT, "proposta.js"), "proposta.js"),
                           (KIT_TOKENS, "tokens.css"),
                           (KIT_LANDING_CSS, "landing.css")):
        if os.path.exists(sorgente):
            shutil.copyfile(sorgente, os.path.join(assets_dir, nome))

    piano = ""
    if args.plausible:
        piano = ('<script defer data-domain="%s" src="https://plausible.io/js/script.js"></script>'
                 % args.plausible)

    titolo = "Preventivo a 3 opzioni: Base, Consigliata, Completa | Preventivi24"
    descrizione = ("Come si presenta un preventivo con tre livelli invece di un solo prezzo. "
                   "Esempi reali di proposte su tre opzioni per aziende e committenti finali.")

    valori = {
        "TITOLO": esc(titolo),
        "DESCRIZIONE": esc(descrizione),
        "URL_CANONICA": esc(url_base + "/"),
        "OG_TITOLO": esc("Un preventivo, tre livelli. Il cliente sceglie il valore."),
        "OG_DESCRIZIONE": esc(descrizione),
        "OG_IMMAGINE": esc(url_base + "/images/og.png"),
        "CSS_HREF": esc("assets/%s/landing.css" % versione),
        "PIANO_SCRIPT": piano,
        "JSON_LD": costruisci_jsonld(url_base),
        "ESEMPI": costruisci_carte(proposte),
        "FAQ": costruisci_faq(),
        "URL_AZIENDE": URL_AZIENDE,
    }
    with open(os.path.join(out_root, "index.html"), "w", encoding="utf-8") as f:
        f.write(tmpl.substitute(valori))

    # --- robots.txt
    robots = (
        "User-agent: *\n"
        "Allow: /\n\n"
        "Sitemap: %s/sitemap.xml\n" % url_base
    )
    with open(os.path.join(out_root, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

    # --- sitemap.xml (solo le pagine indicizzabili)
    voci = ['  <url>\n    <loc>%s/</loc>\n    <priority>1.0</priority>\n  </url>' % url_base]
    for p in indicizzabili:
        voci.append('  <url>\n    <loc>%s/%s/</loc>\n    <priority>0.7</priority>\n  </url>'
                    % (url_base, p["slug"]))
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "\n".join(voci) + "\n</urlset>\n")
    with open(os.path.join(out_root, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    # --- anteprima della landing
    os.makedirs(os.path.join(out_root, "images"), exist_ok=True)
    genera_og_landing(os.path.join(out_root, "images", "og.png"))

    print("Sito pubblico generato in %s" % out_root)
    print("  index.html   robots.txt   sitemap.xml   images/og.png")
    print("Proposte indicizzabili in sitemap: %d su %d" % (len(indicizzabili), len(proposte)))
    rimosse = pulizia_asset(out_root)
    if rimosse:
        print("Asset versione precedente rimossa: %s" % ", ".join(rimosse))
    return 0


if __name__ == "__main__":
    sys.exit(main())
