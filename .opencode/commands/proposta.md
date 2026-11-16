---
description: Genera la proposta a 3 opzioni e la verifica (pagina, anteprima, PDF)
agent: build
---

Genera la proposta `$1` (cartella dentro `proposte/`), poi verifica il risultato
e riporta: prezzi, tempi, scelte, PDF e anteprima.

!`python generatore/genera_proposta.py proposte/$1`

Se il generatore si ferma con errori di validazione, correggi il JSON e rilancia.
Non modificare il generatore per far passare un JSON sbagliato.

Poi controlla il risultato:
- quante pagine ha il PDF
- l'anteprima `og.png` mostra il logo del cliente e il riferimento
- la pagina si apre senza scorrimento orizzontale a 390px
- il nome del committente finale non compare nella pagina se `mostra_cliente` e' false
