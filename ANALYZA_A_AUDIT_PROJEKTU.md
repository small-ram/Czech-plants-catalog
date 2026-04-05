# Analýza A Audit Projektu

Audit byl znovu proveden 4. dubna 2026 nad aktuálním workspace, skripty, SQLite databází, appkou, media vrstvou a dokumentací.

## Shrnutí

Projekt je ve velmi dobrém stavu pro interní používání a další rozvoj. Hlavní posun proti původnímu workbook-only stavu je v tom, že data už mají plnohodnotný životní cyklus:

- workbook
- exporty
- normalizace
- kanonický dataset
- SQLite
- lokální appka
- media vrstva
- build orchestrace
- základní automatizované smoke ověření
- explicitní fallback-promote workflow pro SQLite

Celkově je to silný datově-aplikační prototyp. Není to ale ještě úplně release-ready produkt. Největší zbývající slabiny nejsou v datech samotných, ale v:

- zatím jen částečném pokrytí skutečnými fotkami jako primárním médiem
- stále jen omezené, ne plně regresní test vrstvě
- lehké tendenci k dokumentačnímu driftu mezi iteracemi

## Co bylo ověřeno

### Datová vrstva

- workbook existuje a export pipeline ji znovu načetla bez chyby
- `export_workbook.py` znovu vytvořil raw i normalized výstupy
- `build_v7_canonical.py` znovu vytvořil kanonický dataset
- kanonický dataset obsahuje:
  - `93` plants
  - `193` plant_aliases
  - `242` uses
  - `85` durable_forms
  - `82` sources
  - `301` use_sources

### Kvalita dat

- quality flags jsou snížené na `2` položky
- obě jsou low severity
- jde o nepoužité zdroje `S69` a `S77`

To je velmi dobrý výsledek. V projektu už teď není vidět strukturální datový rozpad.

### SQLite vrstva

- `build_v7_sqlite.py` byl znovu ověřen
- audit dříve odhalil reálný problém:
  skript padal při zamknuté `v7_dataset.sqlite`
- tenhle problém je opraven
- nově skript při locku vytvoří fallback databázi `v7_dataset.rebuild.sqlite` nebo `v7_dataset.rebuild_<timestamp>.sqlite` místo pádu
- navíc existuje explicitní promote režim, který po uvolnění locku přesune fallback na primární místo a původní primární DB zálohuje jako `pre_promote` snapshot
- promote workflow byl ověřen na izolovaném testovacím výstupu

### Lokální appka

- Python server i front-end JS se úspěšně syntax-checkly
- živě byly ověřeny klíčové route pro katalog, plant galerii a detail stránky
- appka stále vrací správné počty a funguje s aktuálním datasetem

### Build a smoke vrstva

- existuje jednotný orchestration skript `build_all.py`
- existuje automatický smoke runner `smoke_check.py`
- oba skripty byly ověřeny reálným během
- `build_all.py` umí nově i volitelný `--promote-rebuild` flow
- vznikají také reporty:
  - `BUILD_PIPELINE_REPORT.md`
  - `SMOKE_CHECK_PROJEKTU.md`

Aktuální smoke coverage ověřuje:

- SQLite tabulky a view
- `/api/summary`
- `/api/options`
- `/api/search`
- `/api/plants`
- `/api/use`
- `/api/plant`
- HTML route `/`, `/plants`, `/plant/...`, `/use/...`
- exporty `/export/plant/...` a `/export/use/...` pro `JSON` i `Markdown`
- základní strukturu export payloadů
- invarianty vybraných filtrů pro durable/core/domain/evidence/month
- očekávané 400/404 chování u vybraných chybových scénářů
- media provenance labely a fotozdroje v detailu/exportech

### Media vrstva

- `plant_media.json` pokrývá všech `93` rostlin
- rozpad primárních médií:
  - `16` skutečných fotek z Wikimedia Commons
  - zbytek má fallback ilustrace nebo auto-cover jen v manifestu
- media provenance je explicitní přes `media_kind`, `source_name`, `source_url` a volitelně `license`
- UI i exporty nově preferují skutečné `Foto`; pokud chybí, ukážou placeholder místo AI coveru

## Silné stránky projektu

### 1. Jasná vícevrstvá architektura

Projekt má zdravé rozdělení odpovědností:

- workbook pro kurátorskou editaci
- exporty pro reprodukovatelnou transformaci
- canonical vrstvu pro strojové použití
- SQLite pro aplikaci
- appku pro lidské používání
- media vrstvu pro vizuální rozšíření
- build a smoke vrstvu pro opakovatelné ověřování

To je silnější než běžný "Excel + pár skriptů" setup.

### 2. Nízký datový dluh

Kvalita dat je vysoká. Zbylé quality flags jsou jen drobné a lokalizované.

### 3. Projekt je už použitelný, ne jen připravený

Už teď lze:

- vyhledávat
- filtrovat
- procházet rostliny
- otevírat detaily
- exportovat JSON a Markdown
- opakovaně rebuildnout a automaticky zkontrolovat hlavní vrstvu aplikace
- bezpečně povýšit fallback SQLite na primární DB bez ruční improvizace

### 4. Dobrá reprodukovatelnost

Pipeline je znovu spustitelná, auditně čitelná a má rozumné chování i v případě zamknuté primární databáze.

## Auditní nálezy

### Nález 1: SQLite rebuild byl křehký při zamknutém cíli

Status:

- nalezeno během auditu
- opraveno
- workflow kolem následného promote je nově explicitní

Dopad:

- build už neselhává při locku
- fallback lze později bezpečně povýšit na primární DB

Zbytkové riziko:

- stále je potřeba lidské rozhodnutí, kdy je vhodný okamžik promote provést

### Nález 2: Dokumentace měla místy drift proti realitě

Status:

- průběžně opravováno
- stále je potřeba držet docs v rytmu s iteracemi

Dopad:

- nízký až střední
- nepoškozuje data ani appku, ale zvyšuje kognitivní load při návratu do projektu

### Nález 3: Media coverage je úplná, ale obsahově je ještě slabá

Status:

- neopraveno
- je to aktuálně hlavní produktové omezení

Faktický stav:

- coverage je `91 / 91`
- ale žádná rostlina zatím nemá skutečnou fotku jako primární médium

Dopad:

- UI působí kompletně, ale vizuální vrstva je stále hlavně fallbacková
- pro interní katalog je to v pořádku
- pro širší prezentaci je to hlavní limit

### Nález 4: Smoke vrstva už existuje, ale ještě není plná regresní sada

Status:

- významně zlepšeno
- stále neuzavřeno

Aktuální stav:

- existuje `smoke_check.py`
- existuje `build_all.py`, který smoke check volá automaticky
- smoke sada ověřuje API, HTML route, exporty, lokální média, záporné scénáře i základní filter invariants

Zbytkové riziko:

- stále chybí širší kombinatorika filtrů, větší invariant coverage a CI běh mimo lokální workflow

### Nález 5: Zbyly 2 nepoužité zdroje

Status:

- neopraveno
- nízká priorita

Detaily:

- `S69`
- `S77`

Dopad:

- minimální
- jde spíš o redakční čistotu než o technický problém

## Celkové hodnocení

### Datová připravenost

Vysoká.

### Reproducibilita

Vysoká pro lokální workflow.

### Aplikační použitelnost

Vysoká pro interní lokální použití.

### Release připravenost pro širší publikaci

Střední.

Hlavní brzda už není architektura ani data, ale:

- chybějící skutečné foto vrstvy
- chybějící plnější automatizace testů mimo smoke úroveň
- potřeba disciplinovaně držet dokumentaci v souladu s iteracemi

## Doporučené další kroky

### Priorita A: Kvalita obsahu

1. Nahradit top auto-covery skutečnými fotkami podle `MEDIA_NAHRADY_PRIORITIZACE.md`.
2. U nejsilnějších rostlin doplnit lepší credits a provenance médií.
3. Vyřešit `S69` a `S77`.

### Priorita B: Testování

1. Rozšířit invariant coverage na další kombinace filtrů a payload detailů.
2. Přidat jednoduchý CI-like lokální release checklist.
3. Zvážit oddělení rychlého smoke a pomalejšího release ověření.

### Priorita C: Produktizace

1. Zvážit static snapshot nebo balitelnou read-only distribuci lokální appky.
2. Ujasnit, jestli má být lokální appka jen interní nástroj, nebo i demonstrační výstup pro další lidi.

## Praktický závěr

Projekt je dnes robustní základ pro lokální znalostní katalog a další produktový rozvoj. Workflow kolem SQLite fallbacku je už výrazně čistší; nejsmysluplnější další investice teď leží hlavně v obsahové vrstvě a v rozšíření test automatizace.
