# Come analizzare i preventivi (procedura assistita, zero costi)

Questo documento descrive il flusso operativo di Scelta24: il confronto lo produce l'assistente, **Gabriele lo controlla prima dell'invio**. Non ci sono API a pagamento: il motore sono le griglie di completezza e la verifica umana.

## 1. Ricezione
- Il committente invia i PDF/contratti via email (dal form contatti con oggetto "Confronto preventivi — Scelta24") o li consegna direttamente.
- Rispondere confermando ricezione e indicando tempi (es. 24-72 ore).

## 2. Lettura e classificazione
- Identificare il tipo di lavoro (bagno, serramenti, fotovoltaico, climatizzazione, altro).
- Aprire la griglia corrispondente in `conoscenza/<tipo>.json`. Se il tipo non esiste, usare le voci più vicine e annotarlo nel metodo.
- Estrarre per ogni preventivo: azienda, prezzo dichiarato, IVA, caparra/pagamenti, tempi, garanzia, voci incluse, esclusioni, clausole notevoli.

## 3. Normalizzazione
Per ogni preventivo compilare:
- **Costo reale stimato** = prezzo dichiarato + IVA (se non inclusa) + stima delle voci mancanti essenziali rispetto alla griglia.
- **Voci mancanti**: confrontare con `voci_obbligatorie` e `voci_opzionali` della griglia.
- **Semafori**: rosso/giallo/verde su impermeabilizzazione/posa, caparra, garanzia, tempi, chiarezza IVA, pratiche/detrazioni, clausole "a misura".

## 4. Verdettto
- La scelta **non** è automaticamente il prezzo più basso: vince il miglior equilibrio tra costo reale, rischi, qualità e tempi.
- Scrivere "perché" in 2-3 frasi comprensibili e 3-5 punti concreti.
- Preparare le domande da inviare alle aziende (voci mancanti, caparra, garanzia, tempi vincolanti, detrazioni).

## 5. Generazione
- Salvare i dati in `analisi/<slug>/analisi.json` (fuori dal repo pubblico se contiene dati reali: usare `--out out`).
- Generare:
  ```bash
  python generatore\analizza.py analisi\<slug> --out out
  ```
  Output: `index.html`, `verdetto.pdf` (1 pagina), `og.png`, `domande.md`.

## 6. Controllo umano (obbligatorio)
Gabriele verifica prima dell'invio:
- i numeri (prezzi, somme, IVA) sono coerenti con i documenti;
- le voci mancanti sono reali e le stime sono ragionevoli;
- il verdetto è motivato e non offensivo verso le aziende;
- non ci sono dati personali non necessari.

## 7. Consegna e privacy
- Inviare il link/report e, se utile, il PDF e le domande.
- **Non pubblicare** analisi con dati reali nel repo git pubblico. Condividerle via cartella privata / Cloudflare Pages protetto (Fase B) o allegati.
- Eliminare i documenti ricevuti dopo la consegna, salvo diverso accordo scritto con il committente.

## Nota
Il confronto è un supporto alla decisione basato sui documenti forniti: non sostituisce un sopralluogo, una perizia tecnica o una consulenza legale. Le stime delle voci mancanti vanno indicate come tali.