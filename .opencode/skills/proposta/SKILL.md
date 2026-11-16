---
name: proposta
description: Preparare, generare e revisionare una proposta a 3 opzioni per un cliente B2B (serramenti, fotovoltaico, climatizzazione, impianti, edilizia). Produce la pagina web che il committente finale apre dal telefono, l'anteprima per WhatsApp e il PDF A4 di due pagine. Invocala quando l'utente chiede di fare un preventivo, una proposta, un preventivo a 3 opzioni, o di sistemare i testi di una proposta esistente.
---

# Skill: Proposta a 3 opzioni

## Quando usarla
- L'utente ha materiali di un cliente (preventivi, listino, foto) e vuole la proposta.
- L'utente chiede di rivedere, correggere o riformattare una proposta esistente.
- L'utente chiede "quanto costa rifare il bagno/serramenti" per un cliente.

## Il contratto dei dati
Tutto parte da `proposte/<slug>/proposta.json`. Il generatore fa il resto:
pagina web, anteprima, PDF.

```bash
python generatore/genera_proposta.py proposte/<slug>
```

Prima di generare, il JSON deve passare la validazione del generatore
(3 opzioni, una sola consigliata, prezzi con tempi, voci per opzione,
riga "perche'"). Se la validazione fallisce, il generatore si ferma: correggi
il JSON, non il generatore.

## Il metodo (le regole del progetto, ereditate da `processo-consegna.md`)

1. **Tre livelli**: Base / Consigliata / Completa. La Consigliata **non** e' la
   piu' cara, e ha una riga "perche' conviene" che regge da sola. Se la riga non
   convince, il livello e' sbagliato: cambia il livello, non la frase.
2. **Prezzi e tempi insieme**: ogni prezzo porta accanto i tempi. Un prezzo senza
   tempi non si scrive.
3. **I prezzi non si inventano**: si ricavano dal listino del cliente e dai
   preventivi persi. Se il listino non c'e', si ricostruiscono le fasce dai
   preventivi e si dichiara la stima.
4. **Ogni numero ha una fonte o la parola "stima"**.
5. **Frasi da massimo 20 parole.** Vietate: eccellenza, innovativo, rivoluzionario,
   qualita' senza compromessi, passione, sogni, soluzioni all'avanguardia.
6. **Il cliente deve capire la differenza in 30 secondi**: 3 card + tabella a
   6-8 criteri con la colonna consigliata in evidenza.
7. **La struttura fissa**: copertina, sintesi, le tre opzioni, confronto rapido,
   cosa e' compreso / cosa non e' compreso, pagamenti e tempi, perche' scegliere
   noi, come confermare.

## Materiali da chiedere al cliente
```
Per partire mi servono quattro cose:
1. 10 preventivi degli ultimi 6 mesi, anche quelli persi (basta il PDF)
2. listino o prezzi di riferimento, anche interno
3. 5-10 foto dei lavori, anche da telefono
4. ragione sociale, P.IVA e indirizzo per la ricevuta
```
Se i preventivi non sono 10, si parte da 3. Se non c'e' listino, si ricostruiscono
le fasce.

## Cosa NON fare
- Non scrivere "accetto" sul pulsante: e' "Scelgo l'opzione". La scelta online non
  e' un accettazione contrattuale (art. 1325 c.c.): la conferma resta sulla firma
  del PDF.
- Non mettere il nome o l'indirizzo del committente finale nella pagina web se
  non e' autorizzato (`cliente_finale.mostra_cliente`). Il `publish_check.py`
  blocca la pubblicazione, anche se il cognome e' finito in un campo testuale.
- Non rendere indicizzabile una proposta reale: resta `noindex` e fuori dalla
  sitemap. Solo le demo sono indicizzabili.
- Non toccare il sito principale (`prova 50\sito`): e' un progetto separato,
  gia' online.

## Controlli prima di dichiarare finito
```bash
python generatore/genera_proposta.py proposte/<slug>
python generatore/build_site.py
python generatore/publish_check.py     # deve passare
```
Poi guarda la pagina a 390px (il committente finale e' sul telefono), il PDF
(deve stare in 2 pagine A4) e l'anteprima (e' quello che si vede su WhatsApp).
