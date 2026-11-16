#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prova.py - genera una proposta di prova completa e la apre nel browser.

Crea un cliente finto "Vetreria Sole" con un brand diverso (verde/blu),
genera la pagina, l'anteprima e il PDF, poi apre il browser e stampa i percorsi.
Serve a vedere che ogni cliente ha il suo brand con lo stesso motore.

Uso:
    python generatore/prova.py
    python generatore/prova.py --out prova-output
"""

import argparse
import json
import os
import subprocess
import sys
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "generatore", "genera_proposta.py")

PROPOSTA = {
    "slug": "prova-vetreria-sole",
    "demo": True,
    "etichetta": "Proposta di prova",
    "riferimento": "2026-PROVA",
    "data": "2026-11-16",
    "valida_fino": "2026-12-16",
    "sopralluogo": "2026-11-14",
    "luogo": "Appartamento, Monza (MB)",
    "intervento": "Sostituzione vetrata del soggiorno",
    "meta_descrizione": "Proposta di prova: tre livelli per la sostituzione di una vetrata scorrevole.",
    "sintesi": "Sostituzione della vetrata scorrevole del soggiorno (3 ante, circa 4,2 m). Tre livelli: dal vetro di base al pacchetto con isolamento acustico e posa certificata.",
    "in_sintesi": "Vetrata scorrevole nuova con smontaggio, posa e smaltimento inclusi. La Consigliata bilancia comfort termico e costo; la Completa aggiunge isolamento acustico e oscurante integrato.",
    "cliente_finale": {
        "nome": "Fam. Bianchi",
        "indirizzo": "Via Roma 12, Monza (MB)",
        "mostra_cliente": False
    },
    "azienda": {
        "nome": "Vetreria Sole",
        "sede": "Monza (MB)",
        "referente": "Luca Ferri",
        "telefono": "039 000 0000",
        "email": "info@vetreriasole-esempio.it",
        "whatsapp": "",
        "cta_email": "russo.enterprise.biz@gmail.com",
        "cta_oggetto": "Vorrei la mia proposta a 3 opzioni - Preventivi24",
        "cta_messaggio": "Buongiorno, ho fatto la prova con Vetreria Sole.\nVorrei la mia proposta su 3 opzioni per la mia attivita'.\nIl mio nome e' ___, la mia azienda e' ___." ,
        "colori": {
            "primario": "#0F766E",
            "accento": "#2563EB",
            "tinta": "#ECFDF5"
        }
    },
    "opzioni": [
        {
            "id": "base",
            "nome": "Base",
            "prezzo": 2450,
            "iva": "22%",
            "tempi": "Consegna 10 giorni · posa 1 giorno",
            "consigliata": False,
            "voci": [
                "Vetro camera 4+12+4",
                "Telaio alluminio bianco standard",
                "Smontaggio della vecchia vetrata",
                "Posa e siliconatura perimetrale",
                "Smaltimento del vetro rimosso"
            ],
            "perche": "Risolve il problema con materiali affidabili e tempi rapidi, al costo piu' contenuto."
        },
        {
            "id": "consigliata",
            "nome": "Consigliata",
            "prezzo": 3180,
            "iva": "22%",
            "tempi": "Consegna 14 giorni · posa 1 giorno",
            "consigliata": True,
            "voci": [
                "Tutto quello della Base",
                "Vetro basso emissivo 4+16+4 per comfort termico",
                "Telaio a taglio termico",
                "Posa certificata, sigillatura e collaudo",
                "Pulizia finale"
            ],
            "perche": "Migliora isolamento e consumi: il miglior equilibrio tra comfort e spesa per un ambiente vissuto ogni giorno."
        },
        {
            "id": "completa",
            "nome": "Completa",
            "prezzo": 4290,
            "iva": "22%",
            "tempi": "Consegna 20 giorni · posa 1-2 giorni",
            "consigliata": False,
            "voci": [
                "Tutto quello della Consigliata",
                "Vetro acustico stratificato per ridurre i rumori",
                "Telaio a taglio termico rinforzato",
                "Tapparella orientabile integrata",
                "Garanzia estesa e assistenza post-posa 12 mesi"
            ],
            "perche": "Massimo comfort e silenzio: ideale se la stanza affaccia su strada o vuoi il pacchetto completo."
        }
    ],
    "confronto": [
        {"criterio": "Tipo di vetro", "base": "Camera standard", "consigliata": "Basso emissivo", "completa": "Acustico stratificato"},
        {"criterio": "Telaio", "base": "Alluminio standard", "consigliata": "Taglio termico", "completa": "Taglio termico rinforzato"},
        {"criterio": "Posa", "base": "Standard", "consigliata": "Certificata + collaudo", "completa": "Certificata + collaudo"},
        {"criterio": "Oscurante integrato", "base": "No", "consigliata": "No", "completa": "Si"},
        {"criterio": "Garanzia posa", "base": "2 anni", "consigliata": "2 anni", "completa": "2 anni + assistenza 12 mesi"}
    ],
    "compreso": [
        "Sopralluogo e rilievo misure",
        "Trasporto materiali",
        "Smontaggio e smaltimento della vecchia vetrata",
        "Garanzia 2 anni sulla posa"
    ],
    "escluso": [
        "Opere murarie non descritte",
        "Pratiche condominiali (se richieste)",
        "Tinteggiature o ripristini oltre il perimetro"
    ],
    "pagamenti": [
        "30% alla conferma dell'ordine",
        "40% a inizio posa",
        "30% a collaudo e consegna"
    ],
    "garanzie": [
        "2 anni sulla posa",
        "Garanzie di fabbrica sui materiali installati"
    ],
    "nota": "Prezzi IVA esclusa. PROPOSTA DI PROVA: dati inventati per verificare il generatore.",
    "privacy_nota": "Documento di prova: non contiene dati reali."
}


def main():
    ap = argparse.ArgumentParser(description="Genera una proposta di prova completa e la apre.")
    ap.add_argument("--out", default=os.path.join(ROOT, "prova-output"), help="cartella di destinazione")
    ap.add_argument("--no-open", action="store_true", help="non aprire il browser")
    args = ap.parse_args()

    out_root = os.path.abspath(args.out)
    cartella = os.path.join(out_root, PROPOSTA["slug"])
    os.makedirs(cartella, exist_ok=True)
    json_path = os.path.join(cartella, "proposta.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(PROPOSTA, f, ensure_ascii=False, indent=2)
        f.write("\n")

    cmd = [sys.executable, GEN, json_path, "--out", out_root]
    print("Genero la proposta di prova...")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(r.returncode)

    index_path = os.path.join(cartella, "index.html")
    pdfs = [n for n in os.listdir(cartella) if n.lower().endswith(".pdf")]
    og = os.path.join(cartella, "og.png")

    print("\n--- PROVA PRONTA ---")
    print("Cliente:   Vetreria Sole (brand verde/blu, diverso dalle demo)")
    print("Pagina:    " + index_path)
    if pdfs:
        print("PDF:       " + os.path.join(cartella, pdfs[0]))
    print("Anteprima: " + og)
    print("\nApri la pagina dal telefono con:  python generatore/serve.py --dir \"" + out_root + "\"")
    print("(serve.py stampa l'indirizzo di rete da aprire sul telefono collegato al wifi)")

    if not args.no_open and os.path.exists(index_path):
        webbrowser.open("file:///" + index_path.replace("\\", "/"))


if __name__ == "__main__":
    main()
