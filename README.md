# České Rostliny

Projekt převádí kurátorovaný workbook o českých rostlinách do použitelné datové, databázové a aplikační vrstvy.

Aktuální stav k 6. dubnu 2026:

- workbook je vyčištěný a auditovaný
- export pipeline funguje z `.xlsx` do `csv/json`
- existuje kanonický `v7` dataset
- existuje SQLite databáze pro lokální dotazy a appku
- existuje lokální webová aplikace pro search, plant galerii a detail stránky
- existuje veřejný statický GitHub Pages build v `docs/`
- existuje explicitní vrstva více metod dlouhodobého potravinového zpracování
- existuje nová vrstva `látky a přínosy`, která vysvětluje proč použití dává smysl a jaké hlavní látky za tím stojí
- jarní repertoár obsahuje i niche a ultra-niche druhy pro březen, duben i květen
- media vrstva pokrývá všech `117` rostlin skutečnými fotkami se zdrojem
- auto-cover položky byly z produkčního manifestu odstraněné
- hlavní katalog i galerie nově umí výchozí sezónní filtr kolem dneška
- každé použití nově nese odvozené `sber_doporuceni`
- existuje jednotný orchestration build, rozšířený smoke check a explicitní fallback-promote workflow pro SQLite

## Hlavní čísla

- `117` rostlin
- `241` aliasů
- `273` použití
- `91` trvanlivých forem
- `109` zdrojů
- `334` vazeb use-source
- `240` vazeb use-processing-method
- `148` použití s aspoň jednou metodou dlouhodobého zpracování
- `72` rostlin s aspoň jedním takovým použitím
- `54` rostlin s trvanlivým použitím
- `41` rostlin v praktickém jádru
- `53` březnových použití napříč `36` rostlinami
- `95` dubnových použití napříč `57` rostlinami
- `126` květnových použití napříč `70` rostlinami
- `117` rostlin s reálnou fotkou v katalogu
- `273` použití s odvozeným `sber_doporuceni`
- `273` použití s `hlavni_prinos_text`
- `93` použití s explicitním `aktivni_latky_text`
- `26` rostlin s kurátorským funkčním profilem
- `96` použití a `57` rostlin v aktuálním sezónním okně `březen + duben` pro datum `2026-04-06`

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
- `docs/`
  veřejný statický web pro GitHub Pages
- `.github/workflows/deploy-pages.yml`
  automatický deploy workflow pro GitHub Pages

## Nejrychlejší workflow

### Jedním příkazem

```powershell
python .\scripts\build_all.py
```

To spustí:

- export workbooku
- build kanonického datasetu
- build SQLite
- build veřejného GitHub Pages webu do `docs/`
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
- přítomnost `hlavni_prinos_text` a `aktivni_latky_text` v detailech a vyhledávání

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
- `LATKY_A_PRINOSY_VRSTA.md`

Shrnutí:

- na začátku měsíce appka výchozí zobrazuje `předchozí + aktuální` měsíc
- pro `2026-04-06` je tedy default `březen + duben`
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

### Veřejná webová verze

GitHub repo:

- `https://github.com/small-ram/Czech-plants-catalog`

GitHub Pages build:

- build skript: `python .\scripts\build_pages_site.py`
- výstup: `docs/`
- deploy workflow: `.github/workflows/deploy-pages.yml`

Cílová veřejná URL:

- `https://small-ram.github.io/Czech-plants-catalog/`

## Důležité dokumenty

- `ANALYZA_A_AUDIT_PROJEKTU.md`
  celkový audit projektu a další doporučené kroky
- `EXPORTY_A_NORMALIZACE.md`
  export pipeline a quality flags
- `V7_KANONICKY_DATASET.md`
  kanonická datová vrstva
- `SQLITE_DATASET.md`
  SQLite vrstva, fallback rebuild a promote workflow
- `LATKY_A_PRINOSY_VRSTA.md`
  nová funkční vrstva vysvětlující přínosy, cílení a hlavní užitečné/aktivní látky
- `METODY_DLOUHODOBEHO_ZPRACOVANI.md`
  vrstva metod dlouhodobého potravinového zpracování
- `DUBNOVE_ROZSIRENI_A_FOTOZDROJE.md`
  přehled všech dubnových kurátorských vln, nových zdrojů a reálných fotozdrojů
- `JARNI_ROZSIRENI_BREZEN_A_KVETEN.md`
  nová březnová a květnová kurátorská vlna, zdroje, fotky a bezpečnostní poznámky k pokročilejším druhům
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
