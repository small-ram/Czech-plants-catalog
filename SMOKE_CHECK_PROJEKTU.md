# Smoke Check Projektu

## Výsledek

- Stav: `PASS`
- Databáze: `C:\Users\Dominik\Documents\ceske rostliny\exports\cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive\v7_canonical\v7_dataset.rebuild_20260406_190729.sqlite`

## SQLite

- plants: 117
- uses: 273
- durable_forms: 91
- sources: 109
- views: 2

## API

- /api/summary plants: 117
- /api/summary uses: 273
- /api/options domains: 7
- /api/options evidence scores: 5
- /api/options months: 12
- /api/options processing methods: 14
- /api/options seasonal default: březen + duben (6. dubna 2026)
- /api/search?q=bez count: 2
- /api/search?seasonal=1 count: 10
- /api/plants count: 20
- /api/plants?seasonal=1 count: 10
- první nalezený media kind v plant galerii: Foto
- aliasy v detailu `r001`: 2
- zdroje v detailu `r001`: 2
- detail `r001` má `sber_doporuceni`: True
- foto test plant: `plant_allium_ursinum`
- foto test use: `r052`
- počet použití v detailu test plant: 1
- source name v detailu test plant: Wikimedia Commons
- media kind v detailu test plant: Foto

## HTML Route

- / status: 200
- /plants status: 200
- /plant/plant_allium_ursinum status: 200
- /use/r001 status: 200

## Exporty

- plant Markdown title: `# česnek medvědí`
- use Markdown title: `# R052 · česnek medvědí`
- plant JSON photos: 1
- use JSON sources: 1

## Filter Invariants

- trvanlivé use výsledky: 10
- jádrové use výsledky: 10
- trvanlivé plant výsledky: 10
- jádrové plant výsledky: 10
- domain filtr `fytoterapie` count: 10
- processing filtr `Sušení` count: 10
- evidence filtr `B` count: 10
- month filtr `1` count: 10

## Negative Scenarios

- missing use status: 404
- missing plant status: 404
- missing use_id status: 400
- invalid export format status: 400
- missing export status: 404

## Media

- lokální media route: `None`
- content-type: `None`

## Co bylo ověřeno

- otevření SQLite databáze
- existence základních tabulek a view
- běh lokálního katalog serveru nad zvolenou DB
- summary endpoint
- options endpoint
- plant index endpoint
- use search endpoint
- sezónní default okno a jeho aplikace v search/plants API
- use detail endpoint
- plant detail endpoint
- standalone HTML route pro katalog, plant detail a use detail
- export route pro plant/use v JSON i Markdown
- základní kontrola struktury export payloadů
- invarianty pro durable/core/domain/evidence/month/processing filtry
- odvozené `sber_doporuceni` v detailu a exportech
- očekávané 400/404 chování u chybových scénářů
- dostupnost media provenance v API
- foto zdroje a provenance v detailu/exportech

