---
description: Revisiona una proposta contro le regole del metodo (non modifica nulla)
agent: revisione
subagent: true
---

Revisiona il file `proposte/$1/proposta.json` contro le regole del metodo e
riporta i problemi. Non modificare il file: solo il rapporto.

Controlla, in quest'ordine:

1. **Tre opzioni** e una sola con `consigliata: true`.
2. **La consigliata non e' la piu' cara.** Se lo e', e' il problema piu' grave:
   segnalalo per primo e spiega quale fascia dovrebbe essere quella consigliata.
3. **Ogni prezzo ha i tempi** accanto (`tempi` non vuoto).
4. **Ogni opzione ha** almeno 5 voci incluse e la riga `perche` (una riga sola).
5. **Frasi da massimo 20 parole** in `sintesi`, `in_sintesi`, `voci`, `perche`.
6. **Parole vietate**: eccellenza, innovativo, rivoluzionario, qualita' senza
   compromessi, passione, sogno, all'avanguardia, unici nel settore.
7. **La tabella di confronto** ha 6-8 criteri, e ogni riga ha un valore per
   tutte e tre le opzioni.
8. **Numeri con fonte o con la parola "stima"** accanto.
9. **Comprese e non comprese**: entrambe le liste non vuote; le esclusioni
   devono essere concrete ("tende e arredi", non "altro").
10. **Dati del committente finale**: se `mostra_cliente` e' false, nessun campo
    testuale deve contenere il nome o il cognome.

Per ogni problema scrivi: il campo, il testo attuale, il testo proposed, e
perche'. Ordina per gravita'. Se non ci sono problemi, dillo e basta.
