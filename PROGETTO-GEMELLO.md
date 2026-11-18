# PROGETTO GEMELLO — Scelta24, lato cliente

> **Aggiornato il 18/11/2026.**
> Il progetto principale (`prova 50`) vende alle aziende la riscrittura dei
> preventivi su tre opzioni. Il gemello fa l'inverso: aiuta il **committente
> finale** a scegliere tra i preventivi/contratti che ha ricevuto.
>
> **Stato: SVILUPPATO E VERIFICATO.** Il confronto è il prodotto principale;
> il generatore di proposte a 3 opzioni resta come strumento B2B e come fonte
> della griglia di completezza.
>
> **Nessun blocco:** non serve Cloudflare per partire. Si usa solo GitHub Pages
> (gratuito) con dati finti per la demo; i dati reali si generano fuori dal repo
> con `--out out` e si consegnano come link privato o PDF. Cloudflare Pages
> resta un'opzione futura, non un prerequisito.

---

## Cosa fa

| Prodotto | Per chi | Input | Output |
|---|---|---|---|
| **Confronto preventivi** (principale) | committente finale | più PDF di preventivi/contratti | tabella normalizzata, costo reale, voci mancanti, semafori, verdetto, domande da inviare alle aziende + `verdetto.pdf` (1 pag) + `og.png` |
| Proposta a 3 opzioni (strumento B2B) | azienda / installatore | `proposte/<slug>/proposta.json` | pagina mobile-first + PDF 2 pagine + anteprima |

Il confronto è prodotto dall'assistente e **controllato da una persona prima
dell'invio**. È un lead magnet gratuito per Preventivi24: nessun abbonamento,
nessuna API a pagamento, nessun dato dei clienti pubblicato.

---

## Cosa c'è (fatto e verificato)

| Cosa | Dove | Stato |
|---|---|---|
| Motore di confronto JSON → pagina + verdetto.pdf + og.png + domande.md | `generatore/analizza.py` | fatto |
| Template e stili del confronto | `kit/confronto.html.tmpl`, `kit/confronto.css` | fatto |
| Griglie di completezza (bagno, serramenti) | `conoscenza/` | fatto |
| Demo pubblica del confronto | `analisi/confronto-demo-bagno/` → `confronto-demo-bagno/` | fatto |
| Generatore proposte a 3 opzioni | `generatore/genera_proposta.py`, `kit/proposta.*` | fatto (strumento B2B) |
| Due proposte dimostrative | `proposte/demo-edilcasa`, `proposte/demo-serramenti` | fatto |
| Landing pubblica (layer SEO) | `index.html`, `kit/landing.html.tmpl`, `generatore/build_site.py` | fatto |
| Controlli prima della pubblicazione | `generatore/publish_check.py` | fatto → **PUBLISH CHECK OK** |
| Server locale per prova da telefono | `generatore/serve.py`, `generatore/prova.py`, `PROVA.md` | fatto |
| Documentazione | `docs/`, `README.md`, `AGENTS.md` | fatto |

**Verifiche passate (18/11/2026):**
- `publish_check.py` → PUBLISH CHECK OK;
- `verdetto.pdf` → 1 pagina A4; PDF proposte → 2 pagine;
- pagine a 390px → nessuno scroll orizzontale (la tabella scorre nel suo
  contenitore `overflow-x:auto`, com'è previsto);
- nessun errore console; CTA "Invia i tuoi preventivi" → form contatti con
  `?servizio=confronto`.

---

## Le fasi

### Fase A — Confronto preventivi (FATTA, prodotto principale)
Il committente finale riceve un link: vede tabella, costo reale, semafori,
verdetto e domande da fare alle aziende. Il verdetto è controllato da una
persona prima dell'invio.

**Si fa così:** `python generatore\analizza.py analisi\<slug>`

### Fase B — Layer SEO pubblico (FATTA)
La landing spiega il metodo, mostra il confronto demo e le due proposte demo,
e rimanda al sito B2B. Cresce quando le proposte reali cominciano a girare e la
landing può citare un caso vero: allora si aggiungono pagine per settore e il
tracciamento delle aperture. Un dominio breve (10-15 €/anno) è opzionale.

### Fase C — Portale B2B (FUTURA, non bloccante)
Il cliente B2B vede proposte, scelte, tempi e report. È il Livello C dell'offerta
(490 €/mese): un canale di ricavo, non una spesa. **Criterio d'ingresso:** almeno
3 clienti reali attivi. Bozza in `docs/fase-c-portale-b2b.md`.

---

### Monetizzazione — modello freemium (entrambe le fasi sopravvivono con le proprie entrate)

Scelta24 è un servizio autonomo, non un cavallo di Troia di Preventivi24. Ha il suo costo (tempo di analisi, lettura contratti, controllo umano) e la sua fonte di entrata.

| Livello | Cosa include | Prezzo | Chi paga |
|---|---|---|---|
| **Gratuito** | Quale preventivo scegliere e perche', costo reale stimato, verdetto in chiaro | 0 € | committente finale (nessun costo) |
| **Completa** | Tabella riga per riga, voci mancanti, semafori di rischio (caparra, garanzia, tempi, detrazioni), domande scritte da inviare alle aziende | 39 € | committente finale |

Il campo `livello` in `analisi/<slug>/analisi.json` (`gratuito` o `completo`) determina cosa mostra il report. Il primo confronto di un cliente è gratis (prova del metodo); dal secondo in poi, o per contratti complessi, si paga.

**Regola:** il committente finale paga, non l'installatore. Se pagasse l'azienda analizzata, il verdetto perderebbe credibilità (conflitto di interessi).

Preventivi24 (l'altro progetto, su terminale separato) resta il servizio B2B per le aziende: riscrittura dei preventivi su 3 opzioni. I due progetti sono separati e devono sopravvivere entrambi con le proprie entrate.

---

## Dove finiscono i dati reali

- **Mai nel repo pubblico.** `.gitignore` esclude `analisi/*/` tranne la demo;
  `publish_check.py` blocca le violazioni.
- **Flusso normale (gratis):** si genera con `--out out` (fuori dal repo) e si
  consegna link privato oppure PDF/allegati. Nessun costo ricorrente.
- **Opzione futura:** Cloudflare Pages (free tier) per link privati con dati
  sensibili. Richiede `npx wrangler login` e un account gratuito. **Non serve
  per partire**, e finché non c'è si procede con GitHub Pages + dati minimi
  (niente nome/indirizzo del committente in pagina; il PDF li mantiene come
  documento ufficiale). I prezzi restano leggibili nel sorgente: va detto al
  cliente e messo per iscritto.

---

## Cosa serve ancora (non blocca)

1. **Nome pubblico**: la cartella si chiama `prova 50 - clienti`, ma per
   l'esterno il servizio è **"Scelta24"** con URL
   `https://gabriruss1.github.io/scelta24/`.
2. **Numero WhatsApp Business** dell'installatore per la CTA delle proposte
   (altrimenti la CTA usa `mailto:`). Non serve per il confronto, il cui flusso
   passa dal form contatti.
3. **Cloudflare (opzionale)**: solo se e quando servono link privati con dati
   reali. Non è un prerequisito.

---

## Documenti

| File | A cosa serve |
|---|---|
| `docs/come-analizzare.md` | procedura assistita: dal PDF ricevuto al verdetto, con controllo umano |
| `docs/passo-passo-per-il-cliente-b2b.md` | cosa riceve il cliente B2B del servizio proposta a 3 opzioni |
| `docs/fase-c-portale-b2b.md` | abbozzo del portale per il cliente B2B |
| `docs/privacy-proposta.md` | ruoli GDPR, dati, cosa non si pubblica |
| `PROVA.md` | prova rapida in 5 passi del confronto |
| `README.md` | panoramica e comandi |
| `AGENTS.md` | regole del progetto per chi ci lavora (anche OpenCode) |
