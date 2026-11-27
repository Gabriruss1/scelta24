#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""config_loader.py — carica config.json unico per tutti i generatori."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT, "config.json")

_config_cache = None


def carica_config():
    """Carica config.json (cached)."""
    global _config_cache
    if _config_cache is None:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = json.load(f)
    return _config_cache


def get(key_path, default=None):
    """Accesso con path a punto: es. get('site.base_url')."""
    cfg = carica_config()
    for k in key_path.split("."):
        if isinstance(cfg, dict) and k in cfg:
            cfg = cfg[k]
        else:
            return default
    return cfg


# --- shortcut per i valori più usati ---

SITE_BASE_URL = get("site.base_url", "https://gabriruss1.github.io/scelta24")
SITE_PREFIX = get("site.prefix", "/scelta24")
EMAIL_CONTATTO = get("contact.email", "russo.enterprise.biz@gmail.com")
FORM_ENDPOINT = get("contact.form_endpoint", f"https://formsubmit.co/{EMAIL_CONTATTO}")
URL_AZIENDE = get("links.aziende", "https://gabriruss1.github.io/preventivi24")
URL_GRAZIE = get("links.grazie", f"{SITE_BASE_URL}/grazie.html")

# URL di contatto per il form e le CTA: assoluti con prefisso
URL_CONTATTO = f"{SITE_BASE_URL}/contatti.html?servizio=confronto"
URL_ANALISI_COMPLETA = f"{SITE_BASE_URL}/contatti.html?servizio=analisi-completa"

CHROME_TIMEOUT_OG = get("generation.chrome_timeout_og", 90)
CHROME_TIMEOUT_PDF = get("generation.chrome_timeout_pdf", 120)
PDF_MAX_PAGINE = get("generation.pdf_max_pages", 1)

# Chrome candidates inclusi Edge
CHROME_CANDIDATI = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/microsoft-edge",
]


def trova_chrome():
    import shutil
    for percorso in CHROME_CANDIDATI:
        if os.path.exists(percorso):
            return percorso
    return shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("msedge")