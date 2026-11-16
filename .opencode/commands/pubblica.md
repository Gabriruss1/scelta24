---
description: Ricostruisce la parte pubblica del sito e passa i controlli di pubblicazione
---

Ricostruisci la parte pubblica del sito (landing, robots, sitemap) e poi esegui
i controlli. Non pubblicare nulla: prima riporta l'esito dei controlli.

!`python generatore/build_site.py`

!`python generatore/publish_check.py`

Riporta:
1. l'esito del publish check (se fallisce, elenca i problemi e correggili)
2. quante pagine sono finite in sitemap (devono essere solo landing e demo)
3. se ci sono proposte reali pubblicate per errore (devono restare noindex)
