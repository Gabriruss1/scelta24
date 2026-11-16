# Fase C — Portale per il cliente B2B

Abbozzo. **Non e' stato deciso se e quando si fa.** Vive qui finche' non
c'e' un cliente che lo chiede e un cliente che lo paga.

---

## Il problema che risolve

Oggi, quando un'azienda compra il servizio, riceve file. La proposta finisce
in una cartella, l'email con la scelta del cliente finale finisce in un'altra,
e tre settimane dopo non si sa piu' quale proposta ha funzionato e quale no.

Il portale mette tutto in un posto solo: le proposte, le scelte, i tempi di
risposta, e un report. E' il Livello C dell'offerta: **490 €/mese**.

## Cosa ci starebbe

### Per l'azienda cliente (si logga)

- **Le sue proposte**: elenco con riferimento, cliente finale, data, stato.
- **Le scelte ricevute**: quale opzione, quando, e il canale (WhatsApp, mail).
- **Il report**: quante proposte, quante risposte, in quanti giorni, tasso di
  scelta per opzione (la Consigliata quanto pesa davvero).
- **Le scadenze**: quali proposte stanno per scadere.
- **I materiali**: listino e template riutilizzabili.

### Per il committente finale

Niente: resta il link. Il portale e' per il cliente B2B.

---

## Cosa lo rende difficile (e perche' rimandato)

| Ostacolo | Perche' non e' banale |
|---|---|
| **Account** | Serve un sistema di identita': registrazione, reset password, due fattori. Non e' piu' un sito statico. |
| **Backend e costi** | Un database e un runtime che gira costano. Finche' si puo' usare il free tier di Cloudflare, i limiti si sentono. |
| **Multi-tenant** | Ogni cliente vede solo i suoi dati. Va progettato bene il modello di permessi, non basta una query con un `WHERE`. |
| **Dati personali** | Il portale conserva i dati dei committenti finali per mesi: base giuridica, informativa, diritti, cifratura, backup. |
| **Manutenzione** | Un backend che nessuno manutiene e' un debito tecnico. Meglio tardi che male. |

## Il percorso_minimo, se un cliente lo chiede

1. **Non costruirlo da zero.** Valutare un servizio gestito con piano free
   (Supabase, Firebase, Airtable + Make) e costruirci sopra solo quello che
   serve: login, tabelle, report. Tempo: qualche giorno, non settimane.
2. **Partire dal report, non dall'area clienti.** Il report (quante proposte,
   quante scelte, quali opzioni) e' il valore vero ed e' anche la cosa piu'
   semplice da costruire: basta registrare gli eventi di scelta.
3. **Registrare gli eventi gia' adesso.** Le scelte arrivano su WhatsApp: si
   possono annotare a mano in un foglio, senza backend. Il giorno in cui
   servirà il portale, si sanno gia' i numeri.

## La decisione, quando arriva

- Serve un cliente che paghi 490 €/mese per il portale? No: si continua con i
  file e il lavoro manuale.
- Quanti clienti attivi? Sotto i 3, il portale e' un costo, non un canale.
- Il sito statico regge? Finche' regge, il sito statico vince: costa zero e
  non si rompe.
