# Build Pipeline Report

## Stav

- Výsledek: `PASS`

## Kroky

- `export_workbook`
  příkaz: `C:\Python312\python.exe C:\Users\Dominik\Documents\ceske rostliny\scripts\export_workbook.py`
  výstup: `Workbook: cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive.xlsx`
- `build_v7_canonical`
  příkaz: `C:\Python312\python.exe C:\Users\Dominik\Documents\ceske rostliny\scripts\build_v7_canonical.py`
  výstup: `Canonical dataset written to: C:\Users\Dominik\Documents\ceske rostliny\exports\cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive\v7_canonical`
- `build_v7_sqlite`
  příkaz: `C:\Python312\python.exe C:\Users\Dominik\Documents\ceske rostliny\scripts\build_v7_sqlite.py`
  výstup: `SQLite database written to: C:\Users\Dominik\Documents\ceske rostliny\exports\cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive\v7_canonical\v7_dataset.sqlite`
- `smoke_check`
  příkaz: `C:\Python312\python.exe C:\Users\Dominik\Documents\ceske rostliny\scripts\smoke_check.py --port 8814 --db C:\Users\Dominik\Documents\ceske rostliny\exports\cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive\v7_canonical\v7_dataset.sqlite`
  výstup: `Smoke check PASS for database: C:\Users\Dominik\Documents\ceske rostliny\exports\cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive\v7_canonical\v7_dataset.sqlite`

## SQLite výstup

- `C:\Users\Dominik\Documents\ceske rostliny\exports\cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive\v7_canonical\v7_dataset.sqlite`
- typ výstupu: `primary`

## Smoke Check

- `Smoke check PASS for database: C:\Users\Dominik\Documents\ceske rostliny\exports\cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive\v7_canonical\v7_dataset.sqlite`
- report: `C:\Users\Dominik\Documents\ceske rostliny\SMOKE_CHECK_PROJEKTU.md`
