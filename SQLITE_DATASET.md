# SQLite Dataset

## Role SQLite vrstvy

SQLite je v projektu hlavní aplikační forma dat mezi kanonickým datasetem a lokální appkou.

Je vhodná pro:

- rychlé lokální dotazy
- debug a exploraci
- search API
- prototypy UI
- LLM nebo RAG pomocné dotazy

## Aktuální stav

Databáze obsahuje:

- `105` plants
- `217` plant_aliases
- `256` uses
- `86` durable_forms
- `95` sources
- `315` use_sources
- `231` use_processing_methods
- `14` vocab_processing_methods

Navíc:

- `142` použití má alespoň jednu metodu dlouhodobého zpracování
- `67` rostlin má alespoň jedno takové použití
- `256` použití má `sber_doporuceni`
- k `2026-04-05` sezónní default vrací `březen + duben`

Připravené view:

- `vw_use_search`
- `vw_durable_core`

## Jak databázi znovu vytvořit

```powershell
python .\scripts\build_v7_sqlite.py
```

Volitelně můžeš určit vlastní výstup:

```powershell
python .\scripts\build_v7_sqlite.py --output .\exports\custom.sqlite
```

Pro kompletní rebuild celé pipeline:

```powershell
python .\scripts\build_all.py
```

## Fallback rebuild chování

Skript je odolný proti zamknutému cílovému souboru.

Pokud je hlavní `v7_dataset.sqlite` právě otevřená jiným procesem:

- rebuild nespadne
- místo toho se vytvoří fallback databáze `v7_dataset.rebuild.sqlite` nebo `v7_dataset.rebuild_<timestamp>.sqlite`
- build vypíše, že šlo o fallback výstup

To je důležité hlavně tehdy, když běží lokální appka a zároveň chceš rebuildnout SQLite vrstvu.

## Jak appka vybírá databázi

`app/catalog_server.py` i `scripts/smoke_check.py` nově vybírají nejčerstvější dostupný SQLite soubor podle času změny.

To znamená:

- pokud je novější fallback `v7_dataset.rebuild*.sqlite` než primární DB, appka i smoke check použijí ten novější soubor
- není nutné čekat s lokálním ověřením až na ruční promote

## Jak povýšit fallback na primary

Po uvolnění locku můžeš nejnovější fallback povýšit na hlavní databázi:

```powershell
python .\scripts\build_v7_sqlite.py --promote-rebuild
```

Volitelně můžeš určit konkrétní rebuild soubor:

```powershell
python .\scripts\build_v7_sqlite.py --promote-rebuild --rebuild-path .\exports\...\v7_dataset.rebuild_20260404_141534.sqlite
```

Promote režim:

- najde rebuild SQLite
- přesune ji na místo primární DB
- původní primární DB zálohuje jako `v7_dataset.pre_promote_<timestamp>.sqlite`

To dává workflow jasnější tvar: build může bezpečně skončit fallbackem a promote se dělá až ve chvíli, kdy je primární DB opravdu volná.

## Smoke check nad konkrétní DB

```powershell
python .\scripts\smoke_check.py --db .\exports\...\v7_dataset.sqlite
```

Smoke check nad zvolenou DB dnes ověřuje:

- základní počty a view v SQLite
- běh lokálního serveru nad konkrétním souborem
- klíčové API endpointy
- standalone HTML route
- exporty `plant/use` v `JSON` a `Markdown`
- invarianty vybraných filtrů včetně `processing_method`
- sezónní default okno a jeho aplikaci v `/api/search` a `/api/plants`
- očekávané 400/404 chování u základních chybových scénářů
- media provenance v detailu a exportech
- `sber_doporuceni` v detailu a exportech

## Tabulky

- `plants`
- `plant_aliases`
- `uses`
- `durable_forms`
- `sources`
- `use_sources`
- `use_processing_methods`
- `vocab_part_categories`
- `vocab_subdomain_categories`
- `vocab_storage_categories`
- `vocab_processing_methods`

## View

### `vw_use_search`

Join přes:

- rostlinu
- použití
- doménu
- část rostliny
- důkaznost
- trvanlivost

Použití:

- faceted search
- rychlé API dotazy
- export do katalogové appky

### `vw_durable_core`

Výběr praktického trvanlivého jádra.

Použití:

- shortlist pro "best of"
- domácí pantry přehled
- landing page nebo onboarding layer

## Praktický závěr

SQLite vrstva je stabilní a dnes už pokrývá:

- vícenásobné metody dlouhodobého zpracování
- sezónní default okno pro appku
- odvozené `sber_doporuceni`

Hlavní další hodnota teď leží spíš v redakčním zpřesnění zdrojových dat než v další infrastrukturní práci.
