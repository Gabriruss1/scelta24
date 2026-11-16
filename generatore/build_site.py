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
URL_CONTATTO = "https://gabriruss1.github.io/preventivi24/contatti.html?servizio=confronto"

FAQ = [
    ("Come faccio a confrontare due o tre preventivi?",
     "Mettili uno accanto all'altro sulla stessa tabella: prezzo dichiarato, IVA, cosa e' incluso, "
     "cosa manca, tempi, caparra e garanzia. Il preventivo piu' basso sulla carta spesso esclude "
     "voci che poi paghi a parte. Scelta24 fa questo confronto riga per riga e ti mostra il costo reale."),
    ("Cosa controllare in un preventivo di ristrutturazione o lavori in casa?",
     "Controlla che ci siano demolizione e smaltimento, impermeabilizzazione, impianti con collaudo, "
     "materiali specificati, tempi scritti, garanzia e condizioni di pagamento. Se una voce e' vaga "
     "o manca, chiedila per iscritto prima di firmare."),
    ("Come si capisce qual e' il preventivo piu' conveniente davvero?",
     "Non basta il prezzo: conta il costo reale. Aggiungi le voci mancanti, verifica IVA e detrazioni, "
     "guarda caparra, garanzia e tempi. Un preventivo piu' economico puo' costare di piu' se esclude "
     "lavori essenziali o scarica rischi su di te."),
    ("Chi gestisce la detrazione fiscale e la pratica CILA?",
     "Dipende dal preventivo: alcuni la includono, altri la lasciano a tuo carico. Va scritto in modo "
     "chiaro perche' ha un costo e serve per la detrazione. Se non e' indicato, e' una domanda da fare "
     "all'azienda prima di scegliere."),
    ("I miei documenti sono al sicuro?",
     "I preventivi e i contratti che ci invii servono solo per il confronto. Non finiscono in un "
     "repository pubblico, non vengono usati per addestrare modelli e vengono eliminati dopo la consegna. "
     "Il risultato viene controllato da una persona prima di arrivarti."),
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


def costruisci_carte(proposte, out_root):
    carte = []
    # confronto demo in evidenza, se presente
    confronto = os.path.join(out_root, "confronto-demo-bagno")
    if os.path.isdir(confronto) and os.path.exists(os.path.join(confronto, "index.html")):
        img = '<img class="esempio__img" src="confronto-demo-bagno/og.png" alt="Anteprima del confronto dimostrativo" loading="lazy">'
        carte.append(
            '<a class="esempio" href="confronto-demo-bagno/">%s'
            '<div class="esempio__corpo"><span>Confronto dimostrativo</span>'
            '<h3>Bagno: preventivo piu\' basso vs costo reale</h3>'
            '<p>Tabella riga per riga, semafori di rischio e verdetto: il piu\' economico non vince.</p></div></a>'
            % img
        )
    for p in proposte:
        if not p["indicizzabile"]:
            continue
        img = ("<img class=\"esempio__img\" src=\"%s/og.png\" alt=\"Anteprima della proposta %s\" loading=\"lazy\">"
               % (esc(p["slug"]), esc(p["slug"])))
        carte.append(
            '<a class="esempio" href="%s/">%s'
            '<div class="esempio__corpo"><span>Esempio di proposta</span>'
            "<h3>%s</h3><p>Tre livelli affiancati: Base, Consigliata, Completa.</p></div></a>"
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
h1{font-size:66px;line-height:1.05;font-weight:600;letter-spacing:-.02em;max-width:940px}
h1 em{font-style:normal;color:#E8A838}
h2{font-size:30px;font-weight:400;opacity:.85;margin-top:26px;max-width:860px;line-height:1.35}
.foot{font-size:24px;opacity:.65;position:relative;letter-spacing:.04em}
</style></head><body>
<div><div class="kick">Confronto preventivi</div>
<h1>Confronta i preventivi. Scegli quello <em>giusto</em>.</h1>
<h2>Costo reale, voci mancanti, rischi e verdetto. Gratis, controllato da una persona prima di arrivarti.</h2></div>
<div class="foot">Scelta24 &middot; un servizio Preventivi24</div>
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
                "name": "Scelta24",
                "url": url_base + "/",
                "inLanguage": "it-IT",
                "description": "Confronto preventivi e contratti: costo reale, voci mancanti, rischi e verdetto. Un servizio Preventivi24.",
                "publisher": {
                    "@type": "Organization",
                    "name": "Preventivi24",
                    "url": URL_AZIENDE,
                },
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
    parser.add_argument("--url-base", default="https://gabriruss1.github.io/scelta24")
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
                           (KIT_LANDING_CSS, "landing.css"),
                           (os.path.join(KIT, "confronto.css"), "confronto.css")):
        if os.path.exists(sorgente):
            shutil.copyfile(sorgente, os.path.join(assets_dir, nome))

    piano = ""
    if args.plausible:
        piano = ('<script defer data-domain="%s" src="https://plausible.io/js/script.js"></script>'
                 % args.plausible)

    titolo = "Scelta24 — Confronta i preventivi e scegli quello giusto"
    descrizione = ("Hai due o tre preventivi sul tavolo? Scelta24 li confronta riga per riga: costo reale, "
                   "voci mancanti, rischi e verdetto. Gratis, controllato da una persona prima di arrivarti.")

    valori = {
        "TITOLO": esc(titolo),
        "DESCRIZIONE": esc(descrizione),
        "URL_CANONICA": esc(url_base + "/"),
        "OG_TITOLO": esc("Confronta i preventivi. Scegli quello giusto."),
        "OG_DESCRIZIONE": esc(descrizione),
        "OG_IMMAGINE": esc(url_base + "/images/og.png"),
        "CSS_HREF": esc("assets/%s/landing.css" % versione),
        "PIANO_SCRIPT": piano,
        "JSON_LD": costruisci_jsonld(url_base),
        "ESEMPI": costruisci_carte(proposte, out_root),
        "FAQ": costruisci_faq(),
        "URL_AZIENDE": URL_AZIENDE,
        "URL_CONTATTO": URL_CONTATTO,
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
    # confronto demo pubblico
    confronto_demo = os.path.join(out_root, "confronto-demo-bagno", "index.html")
    if os.path.exists(confronto_demo):
        voci.append('  <url>\n    <loc>%s/confronto-demo-bagno/</loc>\n    <priority>0.9</priority>\n  </url>' % url_base)
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
