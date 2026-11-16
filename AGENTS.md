# AGENTS.md — regole di questo progetto

Sei il manutentrore del progetto gemello "Preventivi24 — Proposta".
Prima di scrivere qualsiasi cosa, leggi questo file e la skill `proposta`.

## Cosa fa questo progetto

Trasforma un file JSON (`proposte/<slug>/proposta.json`) in:

- una pagina web che il **committente finale** apre dal telefono e in cui sceglie
  una delle tre opzioni;
- un'anteprima 1200x630 (quella che si vede quando il link si condivide su WhatsApp);
- un PDF A4 di due pagine, il documento da archiviare e da firmare.

Non e' un sito vetrina: e' uno strumento di vendita per un'azienda che emette
preventivi. Ogni decisione grafica e' subordinate a questo.

## Comandi (eseguili dalla radice del progetto)

```bash
# rigenera una proposta (pagina + anteprima + PDF)
python generatore\genera_proposta.py proposte\<slug>

# rigenera la parte pubblica (landing, robots, sitemap)
python generatore\build_site.py

# controlli prima di pubblicare: DEVE passare
python generatore\publish_check.py

# tutto insieme, nell'ordine giusto
python generatore\genera_proposta.py proposte\<slug> && python generatore\build_site.py && python generatore\publish_check.py
```

Opzioni utili del generatore:

| opzione | quando |
|---|---|
| `--out out` | genera in una cartella privata, per Cloudflare Pages (proposte reali) |
| `--pubblico` | la pagina e' pubblica: vieta l'uscita dei dati del committente finale |
| `--robots "index, follow"` | solo per le demo: le proposte reali restano `noindex` |
| `--no-pdf --no-og` | ciclo rapido quando si sistema il testo |
| `--url-base https://...` | base degli URL pubblici (GitHub Pages o Cloudflare Pages) |
| `--plausible <dominio>` | statistiche di apertura e di scelta |

## Regole non negoziabili

1. **Tre opzioni, sempre**: Base, Consigliata, Completa. La Consigliata non e'
   la piu' cara e ha una riga "perche' conviene".
2. **Ogni prezzo ha i tempi** accanto. Un prezzo senza tempi non passa la
   validazione e non si genera.
3. **Non si inventano prezzi**: si ricavano dal listino del cliente e dai
   preventivi che ha mandato.
4. **Frasi da massimo 20 parole.** Niente marketing vuoto: vietate "eccellenza",
   "innovativo", "rivoluzionario", "soluzioni all'avanguardia", "passione".
5. **Il pulsante dice "Scelgo l'opzione"**, non "Accetto". La scelta online non
   e' un accettazione contrattuale: la conferma resta sulla firma del PDF.
6. **I dati del committente finale non finiscono in pagina** se non e' stato
   autorizzato (`cliente_finale.mostra_cliente`). Il `publish_check.py` lo
   blocca, anche per il cognome.
7. **Le proposte reali sono `noindex`** e non finiscono nella sitemap. Solo le
   demo sono indicizzabili.
8. **Zero dipendenze obbligatorie**: Python standard. `segno` serve solo per il
   QR (se manca, la pagina funziona lo stesso).

## Stile

- Commenti e testi in italiano, senza accenti nei nomi di file.
- Il design system e' in `kit/tokens.css`: i colori del cliente si cambiano
  da l'override `--brand` / `--brand-ink` (nel `colori` del JSON).
- Non introdurre framework, bundler o dipendenze npm: il sito deve restare
  statico e pubblicabile con un `git push`.
- Il sito principale (`prova 50\sito`) e' un progetto separato e funzionante:
  non lo si tocca.

## Prima di dichiarare finito

- [ ] `python generatore\publish_check.py` passa
- [ ] la pagina si apre a 390px senza scorrimento orizzontale
- [ ] il PDF esce a 2 pagine A4
- [ ] l'anteprima si vede bene come anteprima di link
