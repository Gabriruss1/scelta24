# PROGETTO GEMELLO — Preventivi24, lato cliente

> **Promemoria registrato il 16/11/2026.**
> Il progetto principale (`prova 50`) vende alle aziende la riscrittura dei
> preventivi su tre opzioni. Oggi il committente finale — la persona che riceve
> la proposta — riceve un PDF A4 di due pagine. E' un buon documento, ma:
>
> - su un telefono non si legge: e' troppo denso per uno schermo;
> - in chat (WhatsApp, email) un allegato PDF non si apre, un link si;
> - non si puo' sapere quale opzione e' stata scelta, e quindi non si puo' capire
>   dove il preventivo e' stato perso;
> - il prezzo e' l'unica cosa che il cliente vede, quindi vede solo il prezzo.
>
> **Il progetto gemello colma questo vuoto.** Le tre forme possibili
> (landing per il cliente finale / portale di consultazione delle tre opzioni /
> consegna PDF branded) sono da definire in una fase successiva.
>
> **Stato: item futuro, NON bloccante per il primo incasso.** Nessuna delle fasi
> qui sotto e' un prerequisito per fatturare. Il sito principale
> (`prova 50\sito`, gia' online) continua a funzionare e basta.

---

## Cosa c'e' gia' (Fase A — fatta)

Il nucleo del progetto e' costruito e verificato:

| Cosa | Dove | Stato |
|---|---|---|
| Generatore: JSON -> pagina + anteprima + PDF | `generatore/genera_proposta.py` | fatto |
| Kit di design (colori, tipografia, stampa) | `kit/` | fatto |
| Pagina della proposta (mobile-first, scelta in un tocco) | `kit/proposta.html.tmpl` | fatto |
| Landing pubblica (layer SEO) | `kit/landing.html.tmpl` + `generatore/build_site.py` | fatto |
| Controlli prima della pubblicazione | `generatore/publish_check.py` | fatto |
| Due proposte dimostrative | `proposte/demo-edilcasa`, `proposte/demo-serramenti` | fatto |
| Documentazione | `docs/` | fatto |

Il PDF esce a **2 pagine A4**, la pagina si apre a **390px senza scorrimento
orizzontale**, e l'anteprima e' quella che si vede quando il link si condivide.

---

## Le tre fasi

### Fase A — Microsito di proposta (FATTA)
Il committente finale riceve un link, confronta le tre opzioni, sceglie con un
tocco. La scelta arriva all'installatore su WhatsApp: nessun backend, nessun
dato trattato, nessun form.

**Si fa cosi:** `python generatore\genera_proposta.py proposte\<slug>`

### Fase B — Layer SEO pubblico (FATTA, in minima parte)
La landing `index.html` spiega il metodo, mostra le proposte dimostrative e
rimanda al sito B2B. Serve a due cose: farsi trovare da chi cerca il metodo, e
dare al prospect B2B qualcosa da aprire durante la call.

**Cresce quando:** le proposte reali cominciano a girare, e la landing puo'
citare un caso vero. Allora si aggiungono: un dominio breve (~10-15 €/anno, non
obbligatorio), pagine per settore, e il tracciamento delle aperture.

### Fase C — Portale B2B (FUTURA, e' un canale di ricavo)
Il cliente B2B vede le sue proposte, i suoi committenti finali, e i report: quale
opzione e' stata scelta, dopo quanto tempo, quante aperture.

**Perche' e' rimandata:** richiede account, backend e una scelta di hosting con
costi reali. E' pero' il Livello C dell'offerta (490 €/mese): non e' una spesa,
e' un canale.

**Criterio d'ingresso:** almeno 3 clienti reali attivi. Bozza in
`docs/fase-c-portale-b2b.md`.

---

## Dove finiscono le proposte reali

Due target, entrambi gratuiti:

| Target | Cosa contiene | Perche' |
|---|---|---|
| **GitHub Pages** (`preventivi24-clienti`) | landing, demo, generatore, documenti | il sorgente e' pubblicabile perche' contiene solo dati finti |
| **Cloudflare Pages** (free tier) | le proposte **reali** | il sorgente non finisce mai in un repo pubblico: i prezzi del cliente non sono leggibili da nessuno |

Comando per una proposta reale:

```bash
python generatore/genera_proposta.py proposte\mio-cliente --out out --url-base https://<progetto>.pages.dev
npx wrangler pages deploy out --project-name <progetto>
```

Se Cloudflare non viene usato, il fallback e' GitHub Pages con **dati minimi**:
niente nome e indirizzo del committente finale in pagina (il PDF li mantiene,
e' il documento ufficiale). I prezzi restano leggibili nel sorgente: va detto
al cliente e messo per iscritto.

---

## Cosa serve ancora (non blocca niente)

1. **Account Cloudflare** (gratis) per le proposte reali — oppure conferma
   l'opzione "dati minimi" su GitHub Pages.
2. **Un numero WhatsApp Business** dell'installatore per la CTA (altrimenti
   la CTA usa `mailto:`).
3. **Il nome pubblico**: la cartella si chiama `prova 50 - clienti`, ma per
   l'esterno la proposta consigliata e' **"Preventivi24 — Proposta"** con URL
   `/<azienda>-<riferimento>/`.

---

## Documenti

| File | A cosa serve |
|---|---|
| `docs/privacy-proposta.md` | ruoli GDPR, dati, cosa non si pubblica |
| `docs/passo-passo-per-il-cliente-b2b.md` | cosa riceve il cliente e cosa deve fare |
| `docs/fase-c-portale-b2b.md` | abbozzo del portale per il cliente B2B |
| `AGENTS.md` | regole del progetto per chi ci lavora (anche OpenCode) |
