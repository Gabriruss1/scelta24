# Scelta24 — confronta i preventivi e scegli quello giusto

Lato "cliente finale" di [Preventivi24](https://gabriruss1.github.io/preventivi24/).
Live: https://gabriruss1.github.io/scelta24/

Scelta24 confronta preventivi e contratti riga per riga: **costo reale, voci mancanti, rischi e verdetto**, con le domande da fare alle aziende. Gratis, controllato da una persona prima dell'invio. I documenti non vengono pubblicati ne' usati per addestrare modelli.

Include anche il generatore di **proposte a 3 opzioni** (Base/Consigliata/Completa) usato come strumento e come fonte della griglia di completezza.

## Struttura

- `conoscenza/` — griglie di completezza per tipo di lavoro (il vantaggio: cosa deve esserci)
- `analisi/confronto-demo-bagno/` — dati del confronto dimostrativo pubblico
- `confronto-demo-bagno/`, `demo-edilcasa/`, `demo-serramenti/` — pagine generate
- `generatore/analizza.py` — genera confronto (HTML + verdetto.pdf + og.png + domande.md)
- `generatore/genera_proposta.py` — genera proposta a 3 opzioni (HTML + PDF + og.png)
- `generatore/build_site.py`, `publish_check.py`, `serve.py`, `prova.py`
- `kit/` — design system e template
- `docs/` — privacy, procedura analisi, passo-passo B2B

## Comandi

```bash
# confronto dimostrativo
python generatore/analizza.py analisi/confronto-demo-bagno

# proposta a 3 opzioni (demo)
python generatore/genera_proposta.py proposte/demo-edilcasa --pubblico --robots "index, follow"

# sito pubblico (landing, robots, sitemap) + controlli
python generatore/build_site.py
python generatore/publish_check.py

# prova locale da telefono (stampa IP di rete)
python generatore/serve.py
```

### Flusso operativo (assistito, zero costi API)
1. Il committente invia i PDF dal form contatti (`?servizio=confronto`).
2. Si compila `analisi/<slug>/analisi.json` usando `conoscenza/<tipo>.json` (vedi `docs/come-analizzare.md`).
3. `python generatore/analizza.py analisi/<slug> --out out` (dati reali fuori dal repo).
4. **Controllo umano** e invio. I documenti vengono eliminati dopo la consegna.

Le analisi/proposte reali **non** vanno nel repo pubblico (`publish_check.py` blocca). Deploy link privati: Cloudflare Pages dopo `npx wrangler login` (Fase B).

## Requisiti
- Python 3 (libreria standard)
- Chrome/Edge per PDF e anteprime OG
- `segno` opzionale per QR nelle proposte: `pip install segno`
