# Exporty A Normalizace

## Co tahle vrstva dělá

Vrstva exportů a normalizace převádí workbook do strojově použitelných výstupů bez toho, aby se ztratil původní kurátorský obsah.

Vznikají:

- raw exporty všech listů do `csv`
- raw exporty všech listů do `json`
- normalizovaný export hlavního datasetu
- mapovací tabulky pro problémová pole
- meta soubory se summary a quality flags

## Kde výstupy jsou

Hlavní složka:

- `exports/cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive/`

Uvnitř:

- `raw_csv/`
- `raw_json/`
- `normalized/`
- `meta/`
- `manifest.json`

## Nejdůležitější výstupy

### Normalized starter dataset

- `normalized/starter_dataset_normalized.csv`
- `normalized/starter_dataset_normalized.json`

Obsahuje původní sloupce i odvozená pole jako:

- `record_numeric_id`
- `is_trvanlive_1m_plus`
- `is_jadro_bezne_1m_plus`
- `domena_slug`
- `status_znalosti_slug`
- `aplikovatelnost_slug`
- `dukaznost_rank`
- `obdobi_mesic_od`
- `obdobi_mesic_do`
- `cast_rostliny_skupina`
- `poddomena_kategorie`
- `status_cetnost`

### Mapovací tabulky

V `normalized/`:

- `cast_rostliny_map.csv`
- `poddomena_map.csv`
- `status_v_cr_map.csv`
- `forma_uchovani_map.csv`

### Meta vrstva

V `meta/`:

- `quality_flags.csv`
- `quality_flags.json`
- `workbook_summary.json`

## Aktuální kvalita

Po čištění workbooku a navazujících úpravách jsou quality flags snížené na:

- `2` položky
- obě mají `low` severity
- obě jsou typu `unused_source`

Konkrétně:

- `S69`
- `S77`

To znamená, že exportní a normalizační vrstva je už teď velmi čistá.

## Jak export znovu spustit

```powershell
python .\scripts\export_workbook.py
```

Skript:

- najde workbook `.xlsx`
- načte všechny listy
- vytvoří exporty do `exports/<workbook-stem>/...`

Pro plný workflow přes všechny vrstvy:

```powershell
python .\scripts\build_all.py
```

Tím se export vrstva rovnou propojí s canonical buildem, SQLite buildem, media buildem a závěrečným smoke checkem.

## Silná stránka téhle vrstvy

Nejde jen o technický export. Je to reprodukovatelná mezivrstva mezi editací v Excelu a dalším aplikačním použitím.

## Co dává smysl dál

- uzavřít `S69` a `S77`
- udržet export vrstvu jako první krok jednotného `build_all.py` workflow
- případně přidat několik cílených assertions nad export/meta soubory, pokud by se projekt posouval k release režimu
