#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""publish_check.py — controlli prima della pubblicazione.

Verifica che il sito sia coerente e che non escano dati che non devono
uscire. E' il gate pre-push: se fallisce, non si pubblica.

Uso:
    python generatore/publish_check.py
"""

import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATTERN_VIETATI = [
    (r"\[da inserire\]", "segnaposto rimasto"),
    (r"tel:\+39\b", "link telefono morto"),
    (r"lorem ipsum", "testo di riempimento"),
    (r"cdnjs", "CDN estero"),
    (r"http://fonts\.googleapis", "font servito in chiaro"),
    (r"YOUR_", "segnaposto"),
    (r"undefined", "valore undefined nel sorgente"),
]

FILE_OBBLIGATORI = [
    "index.html",
    "robots.txt",
    "sitemap.xml",
    ".nojekyll",
]

CARTEGGIATE = [
    # (nome file, cosa non deve contenere)
    ("campione-preventivo-serramenti.html", None),
]


def problema(msg):
    return msg


def controlla_file_obbligatori():
    problemi = []
    for nome in FILE_OBBLIGATORI:
        if not os.path.exists(os.path.join(ROOT, nome)):
            problemi.append("manca il file obbligatorio: %s" % nome)
    return problemi


def controlla_pattern():
    problemi = []
    for percorso in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        nome = os.path.basename(percorso)
        with open(percorso, "r", encoding="utf-8") as f:
            contenuto = f.read()
        for pattern, label in PATTERN_VIETATI:
            if re.search(pattern, contenuto, re.IGNORECASE):
                problemi.append("%s: %s" % (nome, label))
        if "</html>" in contenuto and contenuto.split("</html>", 1)[1].strip():
            problemi.append("%s: contenuto dopo </html>" % nome)
    return problemi


def controlla_proposte():
    """Ogni proposta deve avere meta robots, anteprima, PDF e link interni sani."""
    problemi = []
    proposte = [d for d in sorted(os.listdir(ROOT))
                if os.path.isdir(os.path.join(ROOT, d))
                and os.path.exists(os.path.join(ROOT, d, "index.html"))
                and not d.startswith(".") and d not in ("assets", "kit", "generatore",
                                                        "proposte", "docs", "images", ".git",
                                                        ".opencode", ".github")]
    if not proposte:
        problemi.append("nessuna proposta generata: lancia prima il generatore")
    for slug in proposte:
        cartella = os.path.join(ROOT, slug)
        indice = os.path.join(cartella, "index.html")
        with open(indice, "r", encoding="utf-8") as f:
            contenuto = f.read()

        if "<meta name=\"robots\"" not in contenuto:
            problemi.append("%s: manca il meta robots" % slug)

        if not os.path.exists(os.path.join(cartella, "og.png")):
            problemi.append("%s: manca l'anticipa og.png" % slug)

        if not glob.glob(os.path.join(cartella, "*.pdf")):
            problemi.append("%s: manca il PDF" % slug)

        # link interni
        for href in re.findall(r'(?:href|src)="([^"]+)"', contenuto):
            if href.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#")):
                continue
            destinazione = os.path.normpath(os.path.join(cartella, href.split("#")[0]))
            if not os.path.exists(destinazione):
                problemi.append("%s: link rotto -> %s" % (slug, href))
    return problemi


def controlla_privacy():
    """Il dato piu' sensibile e' il nome del committente finale: non deve
    comparire nella pagina pubblicata se non e' stato autorizzato.
    Si controlla sia il nome completo sia il cognome da solo: e' il cognome
    che rende la pagina identificabile."""
    problemi = []
    for percorso_json in sorted(glob.glob(os.path.join(ROOT, "proposte", "*", "proposta.json"))):
        slug = os.path.basename(os.path.dirname(percorso_json))
        indice = os.path.join(ROOT, slug, "index.html")
        if not os.path.exists(indice):
            continue
        with open(percorso_json, "r", encoding="utf-8-sig") as f:
            dati = json.load(f)
        cliente = dati.get("cliente_finale") or {}
        nome = (cliente.get("nome") or "").strip()
        if not nome or cliente.get("mostra_cliente"):
            continue
        with open(indice, "r", encoding="utf-8") as f:
            contenuto = f.read()
        # il cognome: ultima parola di almeno 4 lettere
        parole = [p for p in re.split(r"[\s.]+", nome) if len(p) >= 4 and p[0].isupper()]
        cognome = parole[-1] if parole else ""
        if nome in contenuto:
            problemi.append("%s: dati del committente finale nel testo pubblicato (%s). "
                            "Imposta mostra_cliente=false e rigenera." % (slug, nome))
        elif cognome and cognome in contenuto:
            problemi.append("%s: cognome del committente finale nel testo pubblicato (%s). "
                            "Controlla che non sia finito per sbaglio in un campo." % (slug, cognome))
    return problemi


def controlla_sitemap():
    problemi = []
    percorso = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(percorso):
        return ["sitemap.xml mancante"]
    try:
        tree = ET.parse(percorso)
    except Exception as e:
        return ["sitemap.xml non valido: %s" % e]
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for url in tree.getroot().findall("s:url", ns):
        loc = url.find("s:loc", ns)
        if loc is None or not loc.text:
            problemi.append("sitemap: url senza loc")
            continue
        testo = loc.text.strip()
        coda = testo.split("preventivi24-clienti", 1)[-1].strip("/")
        destinazione = os.path.join(ROOT, coda) if coda else os.path.join(ROOT, "index.html")
        if os.path.isdir(destinazione):
            destinazione = os.path.join(destinazione, "index.html")
        if not os.path.exists(destinazione):
            problemi.append("sitemap: URL non risolvibile -> %s" % testo)
    return problemi


def controlla_noindex():
    """Le proposte reali non devono finire nella sitemap ne' essere indicizzate."""
    problemi = []
    percorso = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(percorso):
        return problemi
    for percorso_json in sorted(glob.glob(os.path.join(ROOT, "proposte", "*", "proposta.json"))):
        with open(percorso_json, "r", encoding="utf-8-sig") as f:
            dati = json.load(f)
        if dati.get("demo"):
            continue
        slug = dati.get("slug")
        indice = os.path.join(ROOT, slug, "index.html")
        if not os.path.exists(indice):
            continue
        with open(indice, "r", encoding="utf-8") as f:
            contenuto = f.read()
        m = re.search(r'<meta name="robots" content="([^"]+)"', contenuto)
        if not m or "noindex" not in m.group(1):
            problemi.append("%s: proposta reale senza noindex" % slug)
        if os.path.exists(percorso):
            with open(percorso, "r", encoding="utf-8") as f:
                if slug in f.read():
                    problemi.append("%s: proposta reale presente in sitemap.xml" % slug)
    return problemi


def main():
    raccolti = []
    raccolti += controlla_file_obbligatori()
    raccolti += controlla_pattern()
    raccolti += controlla_proposte()
    raccolti += controlla_privacy()
    raccolti += controlla_sitemap()
    raccolti += controlla_noindex()

    if raccolti:
        print("PUBLISH CHECK FALLITO (%d problemi):" % len(raccolti))
        for p in raccolti:
            print("  - %s" % p)
        sys.exit(1)
    print("PUBLISH CHECK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
