# Návrh `v7` schématu

Historická poznámka:
tohle je návrhový dokument, ne popis finální implementace. Aktuální stav datového modelu je v `V7_KANONICKY_DATASET.md` a `SQLITE_DATASET.md`.

## Cíl

Další nejlepší krok po auditu není přepsat původní workbook, ale zavést přechodovou vrstvu:

- původní `.xlsx` zůstane jako kurátorský zdroj
- vedle něj vzniknou strojově přátelské exporty
- `v7` schéma oddělí entity, číselníky a vztahy

Tím se zachová obsah i styl kurátorské práce, ale data se stanou výrazně lépe použitelná pro:

- web
- vyhledávání
- filtrování
- analytiku
- AI/RAG
- další kurátorské verze

## Doporučené vrstvy

### 1. Raw layer

Beze změny:

- původní workbook
- případně další budoucí workbook verze

Účel:

- lidská editace
- kurátorský zápis
- zdroj pravdy pro texty

### 2. Export layer

Automaticky generované výstupy:

- `csv`
- `json`
- normalizační mapy
- quality flags

Účel:

- přenos do aplikací
- kontrola kvality
- mezičlánek mezi raw daty a budoucí databází

### 3. Canonical v7 layer

Normalizované tabulky nebo kolekce.

Účel:

- stabilní datový model
- jednotné číselníky
- spolehlivé filtrování
- robustní zdroj pro web nebo API

## Doporučené tabulky

### `plants`

Jedna rostlina nebo taxonomická skupina na řádek.

Doporučená pole:

- `plant_id`
- `vedecky_nazev_hlavni`
- `vedecky_nazev_display`
- `taxon_rank`
- `je_agregat_nebo_spp`
- `cesky_nazev_hlavni`
- `status_v_cr_text`
- `status_puvodnost`
- `status_pestovani`
- `status_zplanovani`
- `status_cetnost`
- `poznamka_taxonomie`

### `plant_aliases`

Synonyma a alternativní názvy.

Doporučená pole:

- `alias_id`
- `plant_id`
- `alias`
- `jazyk`
- `typ_aliasu`
- `je_preferovany`

### `uses`

To je nástupce dnešního `Starter_dataset`.

Jedna položka = jedno konkrétní použití.

Doporučená pole:

- `use_id`
- `plant_id`
- `raw_record_id`
- `cast_rostliny_text`
- `cast_rostliny_kategorie`
- `cast_rostliny_je_kombinovana`
- `domena`
- `domena_slug`
- `poddomena_text`
- `poddomena_kategorie`
- `status_znalosti`
- `status_znalosti_slug`
- `aplikovatelnost_v_cr`
- `aplikovatelnost_slug`
- `typicke_lokality_text`
- `lokality_tagy`
- `obdobi_ziskani_text`
- `mesic_od`
- `mesic_do`
- `fenologicka_faze`
- `zpusob_pripravy`
- `cilovy_efekt`
- `chutovy_profil`
- `vonny_profil`
- `palivovy_potencial_text`
- `hlavni_rizika`
- `kontraindikace_interakce`
- `legalita_poznamka_cr`
- `dukaznost_typ`
- `dukaznost_skore`
- `dukaznost_rank`
- `stav_overeni`
- `kuratorska_poznamka`

### `durable_forms`

Tahle tabulka může stát vedle `uses` nebo být její podmnožinou.

Doporučená pole:

- `durable_id`
- `use_id`
- `forma_uchovani_text`
- `forma_uchovani_kategorie`
- `orientacni_trvanlivost_text`
- `trvanlivost_min_mesice`
- `trvanlivost_max_mesice`
- `poznamka_k_skladovani`
- `is_core_item`
- `proc_je_v_jadru`

### `sources`

Doporučená pole:

- `source_id`
- `nazev`
- `url`
- `typ_zdroje`
- `geograficka_relevance`
- `poznamka`

### `use_sources`

Relační tabulka mezi použitím a zdroji.

Doporučená pole:

- `use_id`
- `source_id`
- `role_zdroje`
- `poradi`
- `poznamka_ke_zdroji`

Tato tabulka je důležitá, protože odstraní omezení `zdroj_id_1` a `zdroj_id_2`.

### `vocab_part_categories`

Číselník pro části rostlin.

Navržené hlavní hodnoty:

- `kvetni_cast`
- `listova_nadzemni_cast`
- `vyhonky_a_pupeny`
- `podzemni_cast`
- `plodova_cast`
- `semena_a_orisky`
- `drevnata_cast`
- `miza`
- `kombinovana_cast`
- `ostatni`

### `vocab_subdomain_categories`

Číselník pro hlavní typy použití.

Navržené hlavní hodnoty:

- `caj_nalev`
- `sirup_koncentrat`
- `liker_macerat`
- `ocet`
- `zavarenina`
- `koreni_dochucovadlo`
- `kavova_nahrada`
- `mouka_skrob`
- `olej`
- `zevni_aplikace`
- `vune_a_vykurovani`
- `palivo`
- `fermentace`
- `suseni_skladovani`
- `cerstva_potrava`
- `odvar`
- `ostatni_specialni`

### `vocab_habitat_tags`

Číselník praktických lokalit.

Navržené tagy:

- `les`
- `okraj_lesa`
- `park`
- `alej`
- `sad`
- `zahrada`
- `mez`
- `remizek`
- `kroviny`
- `ruderal`
- `mokrad`
- `horska_oblast`
- `podhuri`

## Co by mělo zůstat jako text

Některé sloupce má smysl ponechat jako volný text, protože jsou kurátorsky cenné:

- `fenologicka_faze`
- `zpusob_pripravy`
- `cilovy_efekt`
- `hlavni_rizika`
- `kontraindikace_interakce`
- `legalita_poznamka_cr`
- `kuratorska_poznamka`

Jinými slovy:

- kategorizovat to, co se filtruje
- nechat text tam, kde má hodnotu nuance

## Co by mělo být vynuceně normalizované

Tyto oblasti už stojí za pevnější pravidla:

- doména
- poddoména
- část rostliny
- forma uchování
- znalostní status
- aplikovatelnost
- evidence score
- stav ověření
- status v ČR

## Doporučené konvence

### Null / N/A

Použít jen jednu konvenci:

- prázdné = neznámé nebo nedodané
- `N/A` = logicky neaplikovatelné

To je důležité hlavně pro:

- `palivovy_potencial`
- `chutovy_profil`
- `vonny_profil`
- některé speciální poddomény

### Čas

Vedle textu vždy ukládat i strukturu:

- `mesic_od`
- `mesic_do`

### Evidence

Zachovat obě vrstvy:

- `dukaznost_typ`
- `dukaznost_skore`

A přidat:

- `stav_overeni`
- `revidoval`
- `datum_posledni_revize`

## Migrační strategie bez velkého rizika

### Fáze 1

- ponechat workbook beze změn
- generovat exporty a normalizační mapy

### Fáze 2

- založit `v7` číselníky
- doplnit synonymii
- převést zdroje na relační tabulku

### Fáze 3

- z workbooku nebo z JSON exportu vytvořit canonical dataset
- teprve potom řešit web, API nebo AI vrstvu

## Praktický závěr

Nejlepší cesta není „přepsat Excel do databáze naráz“. Lepší je:

- nechat současný workbook jako raw kurátorskou vrstvu
- automaticky z něj dělat exporty
- postupně zavádět normalizaci přes mapovací tabulky

To minimalizuje riziko, zachová obsah a přitom připraví data na další růst.
