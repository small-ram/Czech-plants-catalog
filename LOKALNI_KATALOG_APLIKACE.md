# Lokální Katalog Aplikace

## Co to je

Lokální webová aplikace nad `v7_dataset.sqlite` a `app/media/plant_media.json`.

Je bez externích Python závislostí:

- používá Python standard library
- čte lokální SQLite
- servíruje statický frontend
- umí pracovat s lokálními i externími obrázky

## Kde je kód

- server: `app/catalog_server.py`
- katalog použití: `app/static/index.html`
- galerie rostlin: `app/static/plants.html`
- detail stránky: `app/static/detail.html`
- frontend logika: `app/static/app.js`
- galerie logika: `app/static/plants.js`
- detail logika: `app/static/detail.js`
- styl: `app/static/styles.css`

## Spuštění

```powershell
python .\app\catalog_server.py
```

Volitelně s konkrétní DB:

```powershell
python .\app\catalog_server.py --db .\exports\...\v7_dataset.sqlite
```

Výchozí adresa:

- `http://127.0.0.1:8765`

## Veřejná Pages verze

Vedle lokální Python appky teď existuje i statická veřejná varianta pro GitHub Pages:

- build skript: `scripts/build_pages_site.py`
- výstup: `docs/`
- workflow: `.github/workflows/deploy-pages.yml`
- cílová URL: `https://small-ram.github.io/Czech-plants-catalog/`

## Co appka umí

- fulltext search přes české názvy, vědecké názvy, použití a cílový efekt
- filtrování podle domény, důkaznosti, části rostliny, kategorie použití, měsíce a metody zpracování
- výchozí sezónní režim kolem dneška s bufferem předchozího / následujícího měsíce
- galerii rostlin jako samostatný vstup do katalogu
- detail konkrétního použití
- detail celé rostliny
- standalone stránky `/plant/<plant_id>` a `/use/<use_id>`
- export detailů do `Markdown` a `JSON`
- kopírování odkazů
- hlavní výsledkovou stránku s primární fotkou rostliny přímo na kartě
- odvozené praktické `Jak sbírat správně` v detailech a exportech
- zobrazení provenance fotek přímo v detailu:
  - typ média
  - credit / autor
  - zdrojový odkaz
  - licence, pokud je v manifestu známá

## Důležité chování po dubnovém rozšíření 2026

- katalog jako primární obrázek preferuje jen skutečné `photo` položky
- `illustration` může v manifestu zůstat jako neprimární doprovodné médium, ale galerie ani detail ji neberou jako hlavní fotku
- `/plants` i `/plants/` vrací `200`
- frontend soubory jsou v čistém UTF-8
- server automaticky vybírá nejčerstvější SQLite soubor, tedy i novější `rebuild` fallback
- hlavní katalog i galerie mají zapínatelný sezónní default
- k `2026-04-05` sezónní default vrací `březen + duben`
- při zapnutém sezónním režimu se hlavní stránka i galerie omezují na aktuálně relevantní použití / rostliny

## Co dnes smoke check ověřuje

- `/api/summary`
- `/api/options`
- `/api/search`
- `/api/plants`
- `/api/use`
- `/api/plant`
- HTML route `/`, `/plants`, `/plant/...`, `/use/...`
- export route `/export/plant/...` a `/export/use/...` pro `Markdown` i `JSON`
- základní strukturu export payloadů
- invarianty pro durable/core/domain/evidence/month/processing filtry
- invariant sezónního okna v API
- očekávané `400/404` chování u vybraných chybových scénářů
- přítomnost media provenance a `sber_doporuceni` v API a exportech

## API endpointy

- `/api/summary`
- `/api/options`
- `/api/search`
- `/api/plants`
- `/api/use?use_id=...`
- `/api/plant?plant_id=...`

## Aktuální stav

- `105` rostlin
- `256` použití
- `142` použití s aspoň jednou metodou dlouhodobého zpracování
- `67` rostlin s aspoň jedním takovým použitím
- `105 / 105` rostlin pokrytých reálnou `photo`
- `256 / 256` použití s `sber_doporuceni`
- pro `2026-04-05` sezónní default vrací `105` použití napříč `60` rostlinami

## Silné stránky

- funguje bez frameworkového overkilu
- je rychlá na lokální debug i běžné používání
- dobře sedí na SQLite vrstvu
- exporty i detail stránky jsou součástí automatického smoke ověření
- nové potravinové metody zpracování jsou dostupné jak ve filtrech, tak v detailech
- provenance fotek je dostupná v UI i v `Markdown/JSON` exportech
- fotky jsou i na hlavní výsledkové stránce, ne jen v detailu a galerii
- sezónní default je užitečný, ale pořád transparentní a ručně vypínatelný
- `sber_doporuceni` dává praktický sběrný kontext i tam, kde workbook obsahuje jen surové textové pole

## Co dává smysl dál

- kurátorsky zlepšovat reprezentativnost už doplněných fotek a průběžně kontrolovat licence / kredity
- přidat ještě hlubší invariant checks a release checklist
- převést heuristicky odvozené metody zpracování na explicitní kurátorské pole ve workbooku
