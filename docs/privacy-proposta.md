# Privacy e GDPR — le proposte a 3 opzioni

Documento interno, da conservare. Vale per la pagina di proposta pubblicata
dal progetto gemello (`prova 50 - clienti`).

---

## 1. Chi tratta che cosa

| Soggetto | Ruolo | Dati |
|---|---|---|
| **Il cliente B2B** (es. un serramentista) | **Titolare** | i dati del proprio committente finale, i propri prezzi, il proprio listino |
| **Gabriele Russo** (Preventivi24) | **Fornitore tecnico / responsabile esterno** | i dati tecnici necessari a ospitare e generare la proposta |
| Il committente finale | **Interessato** | nome, indirizzo, dati dell'intervento |

Il cliente B2B resta il titolare: e' lui che ha il rapporto con il proprio
cliente, e il suo cliente finale e' suo. Noi non decidiamo perche' il trattamento
avvenga: lo ospitiamo.

**Da fare:** un incarico (DPA) semplice da far firmare al cliente B2B, con
l'impegno a non usare i dati per altro. Modello pronto in
`docs/incarico-fornitore-treatment.md` (da creare alla prima proposta reale).

---

## 2. Dati che finiscono sulla pagina

| Dato | Nella pagina web | Nel PDF |
|---|---|---|
| Logo, colori, nome del cliente B2B | si | si |
| Prezzi e tempi delle tre opzioni | si | si |
| Riferimento e data della proposta | si | si |
| **Nome del committente finale** | **no, per impostazione** | si |
| **Indirizzo del committente finale** | **no** | si |

Il nome del committente finale e' il dato piu' sensibile: da solo rende la
proposta identificabile, e da solo basta a un concorrente per capire a chi
stai vendendo. Di default non viene pubblicato nella pagina.

Per mostrarlo serve `"mostra_cliente": true` nel JSON **e** il consenso del
cliente B2B. Il controllo automatico (`publish_check.py`) blocca la
pubblicazione se il nome o il cognome finiscono in un campo testuale mentre la
bandierina e' falsa.

---

## 3. Come sono protette le pagine

- `noindex, nofollow` su ogni proposta reale: non finisce in Google, non
  finisce nella sitemap, non viene linkata.
- URL con slug non prevedibile: la pagina non e' un segreto, ma non e'
  cerabile.
- Data di scadenza in pagina: dopo quella data la proposta non e' piu' valida.
  La rimozione dal server e' una decisione operativa, da fare dopo la data.
- Sorgente non pubblico: le proposte reali si pubblicano su Cloudflare Pages,
  il cui codice non e' leggibile da nessuno. Il fallback "dati minimi" su
  GitHub Pages e' accettabile solo se il cliente B2B lo sa e lo accetta per
  iscritto.

---

## 4. Informativa al committente finale

Quando il cliente B2B invia il link, e' lui che informa il proprio cliente
finale (art. 14 GDPR: i dati non sono stati raccolti direttamente da noi).
Il testo da usare:

```
Questa proposta le e' stata inviata da [Azienda], che ha scelto di usare
il servizio di Preventivi24 per prepararla.

I dati su questa pagina (il suo nome, l'indirizzo dell'intervento e i
prezzi) sono trattati da [Azienda], che ne e' il titolare, per inviare e
gestire questa proposta e il rapporto commerciale che ne puo' seguire.
I dati sono conservati per la durata della validita' della proposta e per
i tempi previsti dalla normativa commerciale, dopodiche vengono cancellati.

La scelta che fa qui non e' un accettazione del contratto: la conferma
definitiva avviene con la firma del documento.

Per qualsiasi domanda sui suoi dati puo' scrivere a [Azienda] all'indirizzo
[recapito] o a [indirizzo di Preventivi24].
```

Il pulsante della pagina dice **"Scelgo l'opzione"** e non "Accetto": la scelta
online non e' un accettazione contrattuale (art. 1325 c.c.). La conferma resta
sulla firma del PDF.

---

## 5. Base giuridica e conservazione

- **Base giuridica**: art. 6 par. 1 lett. f) GDPR per quanto riguarda la
  nostra attivita' tecnica (interesse legittimo del fornitore del servizio);
  per il cliente B2B valgono le basi giuridiche sue (art. 6 par. 1 lett. b)
  per la richiesta di preventivo e lett. c) per l'adempimento dell'obbligo
  contrattuale).
- **Conservazione**: la proposta resta valida 20-30 giorni. Passata la data di
  validita', la pagina viene rimossa. Non conserviamo copie delle proposte
  oltre il periodo necessario.
- **Trasferimenti extra-UE**: nessun trasferimento. L'hosting e' su GitHub
  (Microsoft, USA) o Cloudflare: se i dati del committente finale fossero
  salvati su server fuori UE, va valutata la garanzia contrattuale standard.
  Per questo i dati del committente finale **non vengono salvati** nella
  pagina web: restano nel PDF, che e' un file del cliente B2B.

---

## 6. Riferimenti

Da estendere, non da rifare (sono nel progetto principale `prova 50`):

- `docs/legittimo_interesse.md` — LIA per il contatto commerciale B2B
- `docs/dpia_breve.md` — screening WP248
- `privacy-contatti-b2b.md` — registro dei trattamenti per i contatti B2B

Da aggiungere con la prima proposta reale:

- `docs/incarico-fornitore-trattamento.md` — DPA per il cliente B2B
- la riga del committente finale in `privacy-proposta.md` (registro)
