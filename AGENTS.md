# AGENTS.md — regole di questo progetto

Sei il manutentore di **Scelta24** (progetto gemello di Preventivi24).
Prima di scrivere, leggi questo file e i documenti in `docs/`.

## Cosa fa questo progetto

1. **Confronto preventivi/contratti (prodotto principale):** trasforma `analisi/<slug>/analisi.json` in un report che il committente finale apre dal telefono: tabella normalizzata, costo reale, voci mancanti, semafori di rischio, verdetto e domande da inviare. Genera anche `verdetto.pdf` (1 pagina) e `og.png`. Il confronto e' prodotto dall'assistente e **controllato da una persona prima dell'invio**.
2. **Proposta a 3 opzioni (strumento/B2B):** trasforma `proposte/<slug>/proposta.json` in pagina + PDF + anteprima. Le sue voci Base/Consigliata/Completa alimentano le griglie di `conoscenza/`.

Non e' un sito vetrina: e' uno strumento di decisione. Ogni scelta e' subordinata a chiarezza e correttezza.

## Comandi (dalla radice)

```bash
# confronto
python generatore\analizza.py analisi\<slug>
# confronto con dati reali (fuori dal repo)
python generatore\analizza.py analisi\<slug> --out out

# proposta a 3 opzioni
python generatore\genera_proposta.py proposte\<slug>

# sito pubblico e controlli (DEVONO passare)
python generatore\build_site.py
python generatore\publish_check.py
```

## Regole non negoziabili

1. **Verdetto su tutte le dimensioni**: prezzo, rischi, qualita', tempi. Non scegliere mai solo il prezzo piu' basso senza verificare costo reale e omissioni.
2. **Griglia di completezza**: usare `conoscenza/<tipo>.json`; segnalare voci mancanti, caparre alte, tempi vaghi, garanzie ridotte, IVA/pratiche non chiare.
3. **Controllo umano prima dell'invio**: numeri, stime e verdetto vanno verificati. Le stime delle voci mancanti sono esplicite.
4. **Privacy**: documenti/analisi reali **mai** nel repo pubblico; non usati per addestrare modelli; eliminati dopo la consegna. Solo contenuti `demo: true` possono essere pubblicati e indicizzati. `publish_check.py` deve bloccare le violazioni.
5. **Zero costi ricorrenti per l'analisi**: nessuna integrazione che richieda API a pagamento per singola analisi.
6. **Frasi chiare** (max ~20 parole), niente marketing vuoto. Spiegare in italiano semplice.
7. **Proposte a 3 opzioni**: tre opzioni, una consigliata non piu' cara, ogni prezzo con tempi, pulsante "Scelgo l'opzione" (non "Accetto").
8. **Zero dipendenze obbligatorie**: Python standard. Chrome per PDF/OG. `segno` opzionale per QR.
9. **Non toccare** `C:\Users\gabri\Desktop\prova 50\sito` se non per i link/contatti concordati; e' un progetto separato.

## Prima di dichiarare finito

- [ ] `python generatore\publish_check.py` passa
- [ ] demo confronto mostra tabella, semafori, verdetto corretto e domande
- [ ] pagina leggibile a 390px senza scroll orizzontale
- [ ] `verdetto.pdf` esce in 1 pagina A4; PDF proposte in 2 pagine
- [ ] nessun dato reale in repo pubblico
