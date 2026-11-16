# PROVA - Scelta24 (confronto preventivi) in 5 passi

Scelta24 aiuta il **committente finale** a scegliere tra piu' preventivi/contratti: confronto riga per riga, costo reale, semafori di rischio e verdetto. Il risultato e' controllato da una persona prima di arrivare.

Tempo: 5-10 minuti. Meglio dal **telefono**.

---

## 1) Apri l'esempio dal vivo (dal telefono)

Sul PC, nella cartella `C:\Users\gabri\Desktop\prova 50 - clienti`:
```powershell
python generatore\serve.py
```
Sul telefono (stesso wifi) apri l'URL di rete stampato, poi:
- `http://<IP>:8000/confronto-demo-bagno/` — il confronto dimostrativo (caso "wow")
- `http://<IP>:8000/` — la landing

**Cosa controllare:**
- il verdetto dice "Scegli EdilCasa..." anche se BagnoExpress costa meno sulla carta
- tabella con prezzo dichiarato, **costo reale**, voci mancanti
- semafori rosso/giallo/verde e domande da fare alle aziende
- nessuno scroll orizzontale a 390px

---

## 2) Guarda l'anteprima del link e il PDF verdetto

- Anteprima: `confronto-demo-bagno/og.png` (oppure incolla il link live in una chat)
- PDF: `confronto-demo-bagno/verdetto.pdf`

**Cosa controllare:** il PDF e' di 1 pagina A4, mostra verdetto e tabella sintetica; il link/anteprima comunica "confronto preventivi, costo reale, verdetto".

---

## 3) Prova la CTA "Invia i tuoi preventivi"

Dalla landing o dal confronto demo clicca **"Invia i tuoi preventivi"**: deve aprire
`https://gabriruss1.github.io/preventivi24/contatti.html?servizio=confronto`.

**Cosa controllare:**
- oggetto/titolo orientati al confronto ("Confronto preventivi — Scelta24")
- campo "Tipo di lavoro" visibile
- messaggio chiede di allegare/inviare i PDF
- nota privacy: documenti non pubblicati, non usati per addestrare modelli, eliminati dopo la consegna

> Nota: l'invio effettivo via FormSubmit va verificato con un test reale (vedi punto 5).

---

## 4) Verifica le griglie di completezza (il vantaggio)

Apri:
- `conoscenza/bagno.json`
- `conoscenza/serramenti.json`

**Cosa controllare:** voci obbligatorie, extra frequenti e "trappole" (impermeabilizzazione, caparra, garanzia, tempi vaghi, IVA). Sono queste che permettono di dire "costo reale" e non solo "dipende".

---

## 5) Rigenera e controlla (e form end-to-end)

```powershell
python generatore\analizza.py analisi\confronto-demo-bagno
python generatore\genera_proposta.py proposte\demo-edilcasa --pubblico --robots "index, follow"
python generatore\genera_proposta.py proposte\demo-serramenti --pubblico --robots "index, follow"
python generatore\build_site.py
python generatore\publish_check.py
```
`publish_check.py` deve terminare con **PUBLISH CHECK OK**.

**Form end-to-end (da fare una volta, richiede conferma):** invia un messaggio di test da `https://gabriruss1.github.io/preventivi24/contatti.html?servizio=confronto` e verifica che arrivi a `russo.enterprise.biz@gmail.com`.

---

## Flusso operativo (gratis, zero costi API)

1. Il committente invia i PDF dal form/email.
2. L'assistente legge i documenti e compila `analisi/<slug>/analisi.json` usando `conoscenza/<tipo>.json` (vedi `docs/come-analizzare.md`).
3. Si genera il report: `python generatore\analizza.py analisi\<slug> --out out` (fuori dal repo pubblico se dati reali).
4. **Gabriele controlla** numeri e verdetto, poi lo invia. I documenti vengono eliminati dopo la consegna.

Le analisi con dati reali **non** vanno nel repo pubblico (`analisi/*` ignorato, tranne la demo). Cloudflare Pages per link privati: dopo `npx wrangler login` (Fase B).