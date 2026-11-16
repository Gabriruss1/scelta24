# Preventivi24 — Proposta (progetto gemello)

Il lato cliente di [Preventivi24](https://gabriruss1.github.io/preventivi24/).

Il sito principale vende alle aziende la riscrittura dei preventivi su tre
opzioni. Questo progetto costruisce la **proposta che quella azienda manda al
suo cliente finale**: una pagina che si apre dal telefono, con le tre opzioni
affiancate e la scelta in un tocco.

```
prova 50 - clienti/
├── index.html            la landing pubblica (il metodo)
├── demo-edilcasa/        una proposta dimostrativa, generata
├── demo-serramenti/      una proposta dimostrativa, generata
├── assets/<versione>/    css e js condivisi (la versione e' l'hash del kit)
├── generatore/           i programmi
├── kit/                  il design system e i modelli di pagina
├── proposte/             i dati: una cartella per proposta
├── docs/                 privacy, procedura per il cliente, fase C
├── AGENTS.md             le regole del progetto
└── opencode.json         la configurazione di OpenCode per questo progetto
```

## I quattro comandi

```bash
# 1. una proposta nuova (pagina + anteprima + PDF)
python generatore/genera_proposta.py proposte\mio-cliente

# 2. la parte pubblica (landing, robots, sitemap)
python generatore/build_site.py

# 3. i controlli: devono passare prima di pubblicare
python generatore/publish_check.py

# 4. pubblicare
git add -A && git commit -m "..." && git push origin main
```

Per una proposta **reale** (con dati veri) la pagina non va nel repo pubblico:

```bash
python generatore/genera_proposta.py proposte\mio-cliente --out out --url-base https://<progetto>.pages.dev
npx wrangler pages deploy out --project-name <progetto>
```

## Come si scrive una proposta

Tutto parte da `proposte/<slug>/proposta.json`. Il generatore fa il resto e,
se il file non rispetta le regole, si rifiuta di generare.

```jsonc
{
  "slug": "giser-114",
  "riferimento": "2026-114",
  "valida_fino": "2026-12-16",
  "intervento": "Sostituzione serramenti: 7 finestre e 1 portafinestra",
  "sintesi": "…",
  "in_sintesi": "…",
  "cliente_finale": { "nome": "…", "indirizzo": "…", "mostra_cliente": false },
  "azienda": {
    "nome": "Serramenti Giser", "sede": "Rho (MI)",
    "referente": "…", "telefono": "…", "email": "…", "whatsapp": "39…",
    "logo": "images/giser.svg",
    "colori": { "primario": "#12395C", "accento": "#C8952F" }
  },
  "opzioni": [
    { "id": "base", "nome": "Base", "prezzo": 12400, "tempi": "…", "voci": ["…"], "perche": "…" },
    { "id": "consigliata", "nome": "Comfort", "prezzo": 14900, "tempi": "…",
      "voci": ["…"], "perche": "…", "consigliata": true },
    { "id": "completa", "nome": "Completa", "prezzo": 18700, "tempi": "…", "voci": ["…"], "perche": "…" }
  ],
  "confronto": [ { "criterio": "…", "base": "…", "consigliata": "…", "completa": "…" } ],
  "compreso": ["…"], "escluso": ["…"], "pagamenti": ["…"], "garanzie": ["…"]
}
```

**Regole che il generatore fa rispettare:** tre opzioni, una sola consigliata, la
consigliata non e' la piu' cara, ogni prezzo ha i tempi, ogni opzione ha le voci
e la riga "perche'", nessuna parola di marketing vuoto, il confronto ha un
valore per ogni opzione.

## OpenCode in questo progetto

- `/proposta <slug>` — genera e verifica
- `/pubblica` — ricostruisce il sito e passa i controlli
- `/revisiona <slug>` — revisiona il JSON contro le regole (non modifica nulla)
- skill `proposta` — le regole del metodo, per chi prepara una proposta
- `AGENTS.md` — le regole del progetto

## Documenti

- [PROGETTO-GEMELLO.md](PROGETTO-GEMELLO.md) — cosa fa questo progetto e cosa manca
- [docs/privacy-proposta.md](docs/privacy-proposta.md) — ruoli, dati, cosa non si pubblica
- [docs/passo-passo-per-il-cliente-b2b.md](docs/passo-passo-per-il-cliente-b2b.md) — la consegna al cliente
- [docs/fase-c-portale-b2b.md](docs/fase-c-portale-b2b.md) — il portale, quando e se

## Requisiti

- Python 3 (solo libreria standard)
- Chrome installato (per il PDF e le anteprime)
- `segno` (facoltativo, per il QR): `pip install segno`
