# ch.grischamedia.inventree.ean

**EAN / GTIN Unterstützung für InvenTree 0.18** – von **GrischaMedia** (v1.0.0)

## Features
- EAN/GTIN am Teil erfassen (Panel auf der Teile-Detailseite)
- GTIN-Checksumme + Dublettenprüfung
- Speicherung in `Part.metadata['ean']` (kein DB-Schema-Change)
- Scan-Hook: EAN scannen → Teil öffnen
- Mini-Suche: `/plugin/gm-ean/search/?code=...` → Redirect zum Teil

> Hinweis: Das Hinzufügen eines Feldes **im „Teil anlegen“-Dialog** ist in 0.18 per Plugin nicht vorgesehen. Daher Panel-Nachpflege direkt nach dem Anlegen.

## Installation
- Code in den Plugins-Ordner (oder via pip) deployen.
- In InvenTree unter **Einstellungen → Plugins** aktivieren.
- Setting `ENABLE_PANEL` aktiv lassen.

## Lizenz
Proprietär © GrischaMedia. Siehe `LICENSE`.