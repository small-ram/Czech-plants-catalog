# České Rostliny

Projekt převádí kurátorovaný workbook o českých rostlinách do použitelné datové, databázové a aplikační vrstvy.

Aktuální stav k 5. dubnu 2026:

- workbook je vyčištěný a auditovaný
- export pipeline funguje z `.xlsx` do `csv/json`
- existuje kanonický `v7` dataset
- existuje SQLite databáze pro lokální dotazy a appku
- existuje lokální webová aplikace pro search, plant galerii a detail stránky
- existuje explicitní vrstva více metod dlouhodobého potravinového zpracování
- dubnový repertoár obsahuje i niche a ultra-niche druhy
- media vrstva pokrývá všech `105` rostlin skutečnými fotkami se zdrojem
- auto-cover položky byly z produkčního manifestu odstraněné
- hlavní katalog i galerie nově umí výchozí sezónní filtr kolem dneška
- každé použití nově nese odvozené `sber_doporuceni`
- existuje jednotný orchestration build, rozšířený smoke check a explicitní fallback-promote workflow pro SQLite

## Hlavní čísla

- `105` rostlin
- `217` aliasů
- `256` použití
- `86` trvanlivých forem
- `95` zdrojů
- `315` vazeb use-source
- `231` vazeb use-processing-method
- `142` použití s aspoň jednou metodou dlouhodobého zpracování
- `67` rostlin s aspoň jedním takovým použitím
- `49` rostlin s trvanlivým použitím
- `41` rostlin v praktickém jádru
- `86` dubnových použití napříč `50` rostlinami
- `105` rostlin s reálnou fotkou v katalogu
- `256` použití s odvozeným `sber_doporuceni`
- `105` použití a `60` rostlin v aktuálním sezónním okně `březen + duben` pro datum `2026-04-05`

## Struktura projektu

- `cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive.xlsx`
  zdrojový workbook
- `scripts/`
  export, canonical build, SQLite build, media build, Wikimedia fill a orchestration skripty
- `exports/`
  raw exporty, normalizované výstupy, kanonický dataset a SQLite
- `app/`
  lokální katalog aplikace
- `app/media/`
  media manifest a lokální fallback soubory

## Nejrychlejší workflow

### Jedním příkazem

```powershell
python .\scripts\build_all.py
```

To spustí:

- export workbooku
- build kanonického datasetu
- build SQLite
- smoke check nad výslednou databází

Smoke check dnes ověřuje:

- SQLite tabulky a view
- klíčové API endpointy
- standalone HTML route
- exporty `plant/use` v `Markdown` i `JSON`
- invarianty vybraných filtrů
- očekávané `400/404` chování u chybových scénářů
- přítomnost media provenance v API a exportech
- foto zdroje a provenance v detailu i exportech
- invariant filtru `processing_method`
- sezónní default okno a přítomnost `sber_doporuceni`

Vytvoří také:

- `BUILD_PIPELINE_REPORT.md`
- `SMOKE_CHECK_PROJEKTU.md`

### Doplňování reálných fotek

Pro hromadné doplnění nebo obnovu Wikimedia fotek:

```powershell
python .\scripts\fill_wikimedia_photos.py
```

Skript:

- vyhledává přes Wikipedia, Wikidata a Commons
- zapisuje `photo` položky do `app/media/plant_media.json`
- zachovává `credit`, `source_url` a `license`, když jsou dostupné
- vytváří report `MEDIA_WIKIMEDIA_FILL_REPORT.md`

### Sezónní režim a sběr

Podrobnosti k novému chování jsou v:

- `SEZONNI_VYCHOZI_REZIM_A_SBER.md`

Shrnutí:

- na začátku měsíce appka výchozí zobrazuje `předchozí + aktuální` měsíc
- pro `2026-04-05` je tedy default `březen + duben`
- `sber_doporuceni` je odvozené opatrné doporučení postavené na fenologii, části rostliny, lokalitě, rizicích a legalitě

### Když build vytvoří fallback SQLite

Pokud je primární `v7_dataset.sqlite` zamknutá, build zapíše `v7_dataset.rebuild*.sqlite`.

Po uvolnění locku ji můžeš bezpečně povýšit na primární DB:

```powershell
python .\scripts\build_v7_sqlite.py --promote-rebuild
```

Volitelně může orchestrace zkusit promote sama:

```powershell
python .\scripts\build_all.py --promote-rebuild
```

### Po vrstvách

```powershell
python .\scripts\export_workbook.py
python .\scripts\build_v7_canonical.py
python .\scripts\build_v7_sqlite.py
python .\scripts\build_media_covers.py --limit 200 --missing-only
python .\scripts\fill_wikimedia_photos.py
python .\scripts\smoke_check.py
```

### Spuštění lokální appky

```powershell
python .\app\catalog_server.py
```

Výchozí adresa:

- `http://127.0.0.1:8765`

## Důležité dokumenty

- `ANALYZA_A_AUDIT_PROJEKTU.md`
  celkový audit projektu a další doporučené kroky
- `EXPORTY_A_NORMALIZACE.md`
  export pipeline a quality flags
- `V7_KANONICKY_DATASET.md`
  kanonická datová vrstva
- `SQLITE_DATASET.md`
  SQLite vrstva, fallback rebuild a promote workflow
- `METODY_DLOUHODOBEHO_ZPRACOVANI.md`
  vrstva metod dlouhodobého potravinového zpracování
- `DUBNOVE_ROZSIRENI_A_FOTOZDROJE.md`
  přehled všech dubnových kurátorských vln, nových zdrojů a reálných fotozdrojů
- `MEDIA_WIKIMEDIA_FILL_REPORT.md`
  poslední hromadné doplnění Wikimedia fotek
- `LOKALNI_KATALOG_APLIKACE.md`
  lokální appka a její smoke coverage
- `BUILD_PIPELINE_REPORT.md`
  poslední jednotný build report
- `SMOKE_CHECK_PROJEKTU.md`
  poslední smoke check report
- `MEDIA_POKRYTI_A_AUTO_COVERS.md`
  historický report media pokrytí
- `MEDIA_NAHRADY_PRIORITIZACE.md`
  historický prioritizační report pro náhradu placeholderů

## Praktický závěr

Projekt už není jen workbook. Je to funkční lokální znalostní systém s reprodukovatelnou pipeline, relační vrstvou, katalogovou appkou a základní testovací automatizací.

Největší další hodnota teď neleží v nové architektuře, ale v:

- dalším kurátorském rozšiřování jara a léta o regionální a ultra-niche znalosti
- převodu heuristicky odvozených metod zpracování na explicitní kurátorské pole ve workbooku
- zpřesňování rizikových a právních poznámek u nejokrajovějších druhů
- přidání hlubších testů nad filtry a release checklistu
