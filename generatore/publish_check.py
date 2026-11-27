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
    (r"https?://fonts\.googleapis", "font Google Fonts CDN"),
    (r"fonts\.gstatic\.com", "font Google Fonts CDN"),
    (r"YOUR_", "segnaposto"),
    (r"undefined", "valore undefined nel sorgente"),
    (r"gabriruss98@hotmail\.it", "email personale nel codice"),
]

FILE_OBBLIGATORI = [
    "index.html",
    "robots.txt",
    "sitemap.xml",
    ".nojekyll",
]


def controlla_file_obbligatori():
    problemi = []
    for nome in FILE_OBBLIGATORI:
        if not os.path.exists(os.path.join(ROOT, nome)):
            problemi.append("manca il file obbligatorio: %s" % nome)
    return problemi


def controlla_pattern():
    problemi = []
    # scan ricorsivo di tutte le .html pubblicate
    esclusi_dir = {"assets", "kit", "generatore", "proposte", "docs", "images", ".git",
                   ".opencode", ".github", "conoscenza", "analisi", "prova-output", "_chk"}
    for root_dir, dirs, files in os.walk(ROOT):
        # salta directory escluse
        dirs[:] = [d for d in dirs if d not in esclusi_dir and not d.startswith(".")]
        for nome in files:
            if not nome.endswith(".html"):
                continue
            percorso = os.path.join(root_dir, nome)
            with open(percorso, "r", encoding="utf-8") as f:
                contenuto = f.read()
            rel_path = os.path.relpath(percorso, ROOT)
            for pattern, label in PATTERN_VIETATI:
                if re.search(pattern, contenuto, re.IGNORECASE):
                    problemi.append("%s: %s" % (rel_path, label))
            if "</html>" in contenuto and contenuto.split("</html>", 1)[1].strip():
                problemi.append("%s: contenuto dopo </html>" % rel_path)
    return problemi


def cartelle_pubblicate():
    esclusi = {"assets", "kit", "generatore", "proposte", "docs", "images", ".git",
               ".opencode", ".github", "conoscenza", "analisi", "prova-output", "_chk"}
    trovate = []
    for d in sorted(os.listdir(ROOT)):
        cartella = os.path.join(ROOT, d)
        if (os.path.isdir(cartella) and os.path.exists(os.path.join(cartella, "index.html"))
                and not d.startswith(".") and d not in esclusi):
            trovate.append(d)
    return trovate


def controlla_proposte():
    """Ogni pagina pubblicata deve avere meta robots, anteprima, PDF e link interni sani."""
    problemi = []
    pagine = cartelle_pubblicate()
    if not pagine:
        problemi.append("nessuna pagina generata: lancia prima i generatori")
    for slug in pagine:
        cartella = os.path.join(ROOT, slug)
        indice = os.path.join(cartella, "index.html")
        with open(indice, "r", encoding="utf-8") as f:
            contenuto = f.read()

        if "<meta name=\"robots\"" not in contenuto:
            problemi.append("%s: manca il meta robots" % slug)

        if not os.path.exists(os.path.join(cartella, "og.png")):
            problemi.append("%s: manca l'anteprima og.png" % slug)

        if not glob.glob(os.path.join(cartella, "*.pdf")):
            problemi.append("%s: manca il PDF" % slug)

        # link interni
        for href in re.findall(r'(?:href|src)="([^"]+)"', contenuto):
            if href.startswith(("http://", "https://", "mailto:", "tel:", "data:", "#")):
                continue
            # path senza query string e senza fragment
            percorso_href = href.split("#")[0].split("?")[0]
            if href.startswith("/"):
                # link root-relative: si risolve dalla root del progetto
                destinazione = os.path.normpath(os.path.join(ROOT, percorso_href.lstrip("/")))
            else:
                destinazione = os.path.normpath(os.path.join(cartella, percorso_href))
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
    """Ogni URL della sitemap deve corrispondere a un file o a una cartella
    pubblicata. Il prefisso (nome del repo, dominio) puo' cambiare:
    si risolve sull'ultimo segmento del percorso."""
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
        percorso_url = re.sub(r"^https?://[^/]+", "", testo).strip("/")
        segmenti = [s for s in percorso_url.split("/") if s]
        # prova a risolvere sull'ultimo segmento (la cartella della proposta)
        risolto = False
        for segmento in reversed(segmenti):
            cartella = os.path.join(ROOT, segmento)
            if os.path.isdir(cartella) and os.path.exists(os.path.join(cartella, "index.html")):
                risolto = True
                break
        if not risolto:
            if os.path.exists(os.path.join(ROOT, "index.html")):
                risolto = True
        if not risolto:
            problemi.append("sitemap: URL non risolvibile -> %s" % testo)
    return problemi


def controlla_noindex():
    """Le proposte e analisi reali non devono finire nella sitemap ne' essere indicizzate."""
    problemi = []
    percorso = os.path.join(ROOT, "sitemap.xml")
    sitemap_txt = ""
    if os.path.exists(percorso):
        with open(percorso, "r", encoding="utf-8") as f:
            sitemap_txt = f.read()

    for percorso_json in sorted(glob.glob(os.path.join(ROOT, "proposte", "*", "proposta.json"))):
        with open(percorso_json, "r", encoding="utf-8-sig") as f:
            dati = json.load(f)
        if dati.get("demo"):
            continue
        slug = dati.get("slug") or os.path.basename(os.path.dirname(percorso_json))
        indice = os.path.join(ROOT, slug, "index.html")
        if not os.path.exists(indice):
            continue
        with open(indice, "r", encoding="utf-8") as f:
            contenuto = f.read()
        m = re.search(r'<meta name="robots" content="([^"]+)"', contenuto)
        if not m or "noindex" not in m.group(1):
            problemi.append("%s: proposta reale senza noindex" % slug)
        if sitemap_txt and ("/%s/" % slug) in sitemap_txt:
            problemi.append("%s: proposta reale presente in sitemap.xml" % slug)

    # analisi: solo le demo possono essere pubblicate nel repo
    for percorso_json in sorted(glob.glob(os.path.join(ROOT, "analisi", "*", "analisi.json"))):
        with open(percorso_json, "r", encoding="utf-8-sig") as f:
            dati = json.load(f)
        slug = dati.get("slug") or os.path.basename(os.path.dirname(percorso_json))
        indice = os.path.join(ROOT, slug, "index.html")
        if dati.get("demo"):
            if os.path.exists(indice):
                with open(indice, "r", encoding="utf-8") as f:
                    contenuto = f.read()
                m = re.search(r'<meta name="robots" content="([^"]+)"', contenuto)
                if not m or "index" not in m.group(1):
                    problemi.append("%s: confronto demo dovrebbe essere indicizzabile" % slug)
            continue
        # non demo: non deve esserci cartella pubblicata ne' in sitemap
        if os.path.exists(indice):
            problemi.append("%s: analisi reale pubblicata nel repo (rimuovi la cartella generata)" % slug)
        if sitemap_txt and ("/%s/" % slug) in sitemap_txt:
            problemi.append("%s: analisi reale presente in sitemap.xml" % slug)
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
