# Sezónní Výchozí Režim A Sběr

## Co se změnilo

Projekt nově přidal dvě vrstvy navíc:

- výchozí sezónní filtr kolem dneška pro `/` i `/plants`
- odvozené pole `sber_doporuceni` pro každé použití

K 5. dubnu 2026 se výchozí sezónní okno nastavuje na:

- `březen + duben`

V aktuálním datasetu to znamená:

- `105` použití relevantních pro `březen + duben`
- `60` rostlin s alespoň jedním takovým použitím

## Sezónní logika

Logika je úmyslně jednoduchá a čitelná:

- `1.–10.` den v měsíci: předchozí + aktuální měsíc
- `11.–21.` den v měsíci: předchozí + aktuální + následující měsíc
- `22.–konec` měsíce: aktuální + následující měsíc

Příklad:

- `2026-04-05` => `březen + duben`

Uživatel může sezónní režim v UI vypnout a vrátit se k plnému katalogu nebo ručnímu měsíčnímu filtru.

## `sber_doporuceni`

Pole `sber_doporuceni` je nové odvozené praktické doporučení.

Není to ručně psaný botanický postup pro každý druh zvlášť. Místo toho se generuje opatrně z kombinace:

- `cast_rostliny`
- `cast_rostliny_skupina`
- `obdobi_ziskani`
- `fenologicka_faze`
- `typicke_lokality_v_CR`
- `hlavni_rizika`
- `legalita_poznamka_CR`

Odvozený text má být:

- konkrétní
- praktický
- opatrný
- bez neověřených druhově specifických čísel nebo limitů

Aktuálně platí:

- `256 / 256` použití má vyplněné `sber_doporuceni`

## Jaká pravidla se odvozují

- fenologické načasování sběru
- část-rostliny-specifická šetrnost:
  - listy
  - květy
  - plody
  - semena
  - kořeny / oddenky
  - kůra / dřevo
  - pupeny / výhonky
  - míza
- opatrnost vůči kontaminaci
- opatrnost u mokřadních a vodních stanovišť
- upozornění na riziko záměny
- respekt k povolení, cizím pozemkům a chráněným režimům
- základní hygienu sběru a rychlé zpracování

## Důležité omezení

`sber_doporuceni` je odvozená vrstva. To znamená:

- použití a jeho smysl stále stojí primárně na kurátorských datech a zdrojích v datasetu
- `sber_doporuceni` nepředstírá, že nahrazuje druhově specifickou monografii
- tam, kde je v datech explicitní právní nebo riziková poznámka, má přednost ona

## Zdroje, o které se odvození opírá

Pro obecné zásady sběru a hygieny byla logika zpřesněná podle těchto zdrojů:

- [EMA: Guideline on Good Agricultural and Collection Practice (GACP) for starting materials of herbal origin](https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-good-agricultural-collection-practice-gacp-starting-materials-herbal-origin-superseded_en.pdf)
- [AHPA: Guidance on Wild Collection](https://www.ahpa.org/Files/GACP-GMP/GACP-GMP-Sections/2024/AHPA_GACP-GMP_Guidance_Section%204_Wild%20Collection.pdf)
- [Ministerstvo životního prostředí ČR: Přírodní rezervace](https://mzp.gov.cz/cz/agenda/priroda-a-krajina/zvlaste-chranena-uzemi/prirodni-rezervace)

Konkrétní použití jednotlivých rostlin dál vycházejí hlavně z kurátorských zdrojů v samotném workbooku a canonical datasetu.
