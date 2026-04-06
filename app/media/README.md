# Plant Media Manifest

Tahle složka drží media manifest pro katalog a případné lokální fallback soubory.

## Stav k 6. dubnu 2026

- manifest pokrývá všech `117` rostlin v datasetu
- všech `117` rostlin má skutečnou fotku z Wikimedia zdrojů
- auto-cover položky i soubory byly odstraněné
- API a UI tedy už nemusí spoléhat na placeholder-only stav žádné rostliny

## Jak funguje manifest

Soubor `plant_media.json` mapuje `plant_id` na seznam médií.

Každá položka může nést:

- `src`
- `alt`
- `caption`
- `credit`
- `source_name`
- `source_url`
- `license`
- `media_kind`

Povolené hodnoty `media_kind`:

- `photo`
- `illustration`

## Důležité chování

- katalog a exporty preferují pouze `photo`
- pokud by některá rostlina ztratila `photo`, UI umí spadnout zpět na placeholder
- `source_url` a `license` jsou volitelné, ale pro nové reálné fotky doporučené

## Příklad

```json
{
  "plant_allium_ursinum": [
    {
      "src": "https://commons.wikimedia.org/wiki/Special:FilePath/Allium%20ursinum.jpg",
      "alt": "Česnek medvědí v květu a listu",
      "caption": "Wikimedia Commons: Allium ursinum",
      "credit": "Meneerke bloem",
      "source_name": "Wikimedia Commons",
      "source_url": "https://commons.wikimedia.org/wiki/File:Allium_ursinum.jpg",
      "license": "CC BY-SA 4.0",
      "media_kind": "photo"
    }
  ]
}
```

## Zdroj `src`

Může být:

- lokální soubor v téhle složce
- plná webová URL

Aktuální produkční stav používá primárně webové Wikimedia URL.

## Jak zjistit `plant_id`

- `exports/.../v7_canonical/json/plants.json`
- `exports/.../v7_canonical/csv/plants.csv`

## Skripty

### Historické fallback cover workflow

```powershell
python .\scripts\build_media_covers.py --limit 200 --missing-only
```

Tohle už není součást běžného `build_all.py`. Zůstává jen jako ruční nouzový nástroj, pokud by někdy vznikla nová rostlina úplně bez fotky.

### Hromadné doplnění skutečných fotek

```powershell
python .\scripts\fill_wikimedia_photos.py
```

Skript:

- prochází rostliny z SQLite datasetu
- hledá fotky přes Wikipedia, Wikidata a Wikimedia Commons
- zapisuje `photo` položky do manifestu
- zachovává nebo doplňuje `credit`, `source_name`, `source_url` a `license`
- vytváří report `MEDIA_WIKIMEDIA_FILL_REPORT.md`

## Praktický další krok

Nejdůležitější práce v téhle vrstvě teď už není základní pokrytí, ale kvalita:

- ruční výběr reprezentativnějších fotek tam, kde automat našel jen první slušný výsledek
- případné sjednocení stylu u kombinovaných taxonů typu `spp.` nebo více druhů v jednom záznamu
