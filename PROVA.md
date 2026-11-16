# PROVA - Scelta24 in 5 passi

Usa questa guida per vedere il progetto come lo vedra' il cliente finale.
Tempo: 5-10 minuti. Meglio dal **telefono** (e' li' che si apre la proposta).

---

## Prima di iniziare

1. Assicurati di avere Python installato (`python --version`).
2. (Opzionale ma consigliato) Chiudi Chrome per risultati piu' stabili nella generazione di PDF/anteprima.
3. Apri un terminale nella cartella del progetto: `C:\Users\gabri\Desktop\prova 50 - clienti`

---

## 1) Apri la demo sul telefono (wifi di casa)

Nel terminale:

```powershell
python generatore\serve.py
```

Il comando stampa due indirizzi. Sul telefono, collegato allo **stesso wifi** del PC, apri quello di rete, ad esempio:

- `http://192.168.1.34:8000/demo-edilcasa/`
- `http://192.168.1.34:8000/demo-serramenti/`

**Cosa controllare:**
- la pagina si legge bene, niente scroll orizzontale
- le 3 opzioni (Base, Consigliata, Completa) sono chiare
- il pulsante **"Scelgo l'opzione"** apre la mail con testo gia' pronto
- in fondo c'e' la fascia **"Questa e' una proposta dimostrativa... Parliamone"** che porta ai contatti

---

## 2) Guarda l'anteprima del link (come su WhatsApp)

Quando condividi il link, WhatsApp/email mostra un'anteprima (titolo, testo, immagine). Per simularla:
- apri `https://gabriruss1.github.io/scelta24/demo-edilcasa/` e incolla il link in una chat con te stesso, oppure
- controlla il file `demo-edilcasa/og.png` (immagine 1200x630).

**Cosa controllare:** il titolo e l'immagine fanno capire che e' "una proposta su 3 opzioni" e portano il nome Scelta24/azienda.

---

## 3) Stampa il PDF e guarda il QR

Apri il PDF della demo:
- `demo-edilcasa/Proposta-edilcasa-di-gabriele-romano-2026-114.pdf`

**Cosa controllare:**
- il PDF e' di **2 pagine A4**, leggibile
- in fondo alla pagina 2 c'e' il **QR** che punta alla proposta online
- il riquadro riassuntivo mostra le 3 opzioni e quella consigliata

(Se il PDF non si genera, verifica che Google Chrome/Edge sia installato: il generatore lo usa in modalita' headless.)

---

## 4) Clicca "Scelgo l'opzione" e guarda cosa parte

Sulla pagina demo, clicca **Scelgo l'opzione** su una delle tre schede.

**Cosa controllare:**
- si apre il client di posta (`mailto:`) indirizzato a `russo.enterprise.biz@gmail.com`
- oggetto: "Vorrei la mia proposta a 3 opzioni - Preventivi24"
- testo gia' compilato: chiede una proposta per la propria attivita' (non "scelgo Base/Comfort" del finto cliente)

> Nota: WhatsApp e' rimandato. Quando ci sara' `azienda.whatsapp` nel JSON, lo stesso pulsante aprira' WhatsApp invece della mail.

---

## 5) Prova completa con un cliente finto (brand diverso)

Genera una proposta nuova per "Vetreria Sole" (verde/blu, azienda diversa dalle demo):

```powershell
python generatore\prova.py
```

Il comando:
- crea la proposta in `prova-output/prova-vetreria-sole/`
- genera pagina + `og.png` + PDF
- apre il browser sulla pagina
- stampa i percorsi dei file

Poi, per aprirla dal telefono:

```powershell
python generatore\serve.py --dir prova-output
```

e apri `http://<IP-stampato>:8000/prova-vetreria-sole/` dal telefono.

**Cosa controllare:** colori e nome sono di Vetreria Sole, ma struttura e pulsanti sono gli stessi. Questo dimostra che **ogni cliente ha il suo brand con lo stesso motore**.

---

## Verifica automatica (opzionale)

Dalla root del progetto:

```powershell
python generatore\build_site.py
python generatore\publish_check.py
```

`publish_check.py` deve terminare con `PUBLISH CHECK OK`.

---

## Note

- Le demo pubblicate sono fittizie e indicizzabili. Le **proposte reali** non vanno nel repo pubblico (gate privacy attivo, deploy previsto su Cloudflare Pages).
- Cloudflare Pages (proposte reali, link privati): richiede `npx wrangler login` una volta (account esistente). Vedi `docs/passo-passo-per-il-cliente-b2b.md`.
- Se qualcosa non torna, i file generati sono in `demo-edilcasa/`, `demo-serramenti/` e `prova-output/`.
