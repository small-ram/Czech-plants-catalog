# V7 Kanonický Dataset

## Co tahle vrstva představuje

Kanonický dataset je mezivrstva mezi raw/normalized exporty z workbooku a SQLite databází.

Je vhodná pro:

- importy do databází
- API a lokální appku
- další transformace
- analytické dotazy bez přímé závislosti na workbooku
- LLM nebo RAG workflow

## Aktuální obsah

Ve `v7_canonical/` jsou dvě hlavní formy:

- `csv/`
- `json/`

Aktuální počty:

- `plants`: `117`
- `plant_aliases`: `241`
- `uses`: `273`
- `durable_forms`: `91`
- `sources`: `109`
- `use_sources`: `334`
- `use_processing_methods`: `240`
- `vocab_processing_methods`: `14`

Navíc dnes platí:

- `148` použití má alespoň jednu metodu dlouhodobého zpracování
- `72` rostlin má alespoň jedno takové použití
- `273` použití má odvozené `sber_doporuceni`
- `273` použití má `hlavni_prinos_text`
- `82` použití má explicitní use-level `aktivni_latky_text`
- `54` použití má explicitní use-level `latky_a_logika_text`
- `26` rostlin má kurátorský funkční profil

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

## Modelová logika

### `plants`

Jedna entita pro jednu hlavní botanickou identitu používanou v datasetu.

### `plant_aliases`

Aliasová vrstva pro:

- alternativní české názvy
- vědecké varianty
- lepší vyhledávání

### `uses`

Hlavní tabulka konkrétních použití. Nese:

- vazbu na `plant_id`
- normalizovaná pole
- parsed měsíce
- flagy pro trvanlivost a praktické jádro
- agregovaná pole `processing_methods_text`, `processing_methods_count` a `ma_potravinove_konzervacni_metody`
- pole `sber_doporuceni`, tedy odvozené praktické doporučení ke sběru
- novou funkční vrstvu `hlavni_prinos_text`, `aktivni_latky_text`, `latky_a_logika_text` a `funkcni_kontext_status`

`sber_doporuceni` se dnes odvozuje z kombinace:

- `cast_rostliny`
- `cast_rostliny_skupina`
- `obdobi_ziskani`
- `fenologicka_faze`
- `typicke_lokality_v_CR`
- `hlavni_rizika`
- `legalita_poznamka_CR`

### `durable_forms`

Odvozená vrstva pro trvanlivé formy a praktické jádro.

Nově také nese:

- `processing_methods_text`
- `processing_methods_count`

### Funkční vrstva přínosů a látek

Na `plants` i `uses` nově existují pole:

- `hlavni_prinos_text`
- `aktivni_latky_text`
- `latky_a_logika_text`
- `funkcni_kontext_status`

Použití:

- rychlejší pochopení, proč je daná položka prakticky zajímavá
- vysvětlení „na co to míří“ bez nutnosti číst celý popis
- vyhledávání přes látky a benefity

`funkcni_kontext_status` dnes rozlišuje:

- `kuratorsky_profil`
- `odvozeno_z_pouziti`
- `bez_kuratorskeho_profilu`

### `use_processing_methods`

Many-to-many vrstva mezi jedním použitím a více metodami dlouhodobého zpracování.

To je důležité proto, že jedna položka může reálně zahrnovat víc možností současně, například:

- sušení
- sirup
- zavaření
- džem
- kompot

### `vocab_processing_methods`

Slovník metod dlouhodobého zpracování. Aktuálně obsahuje:

- `Sušení`
- `Mražení`
- `Skladování v chladu`
- `Sirup / koncentrát`
- `Zavaření / sterilace ve sklenici`
- `Pasterace`
- `Sterilizace`
- `Kvašení / fermentace`
- `Naložení do octa / ocet`
- `Naložení do oleje / olej`
- `Tinktura / alkoholová macerace`
- `Cukrování / kandování / džem`
- `Kompot`
- `Nakládání`

### `sources` a `use_sources`

Relační zdrojová vrstva pro vícezdrojové použití.

## Odkud se metody zpracování berou

Aktuální `v7` vrstva je odvozuje heuristicky z několika textových polí:

- `poddomena`
- `zpusob_pripravy_nebo_vyuziti`
- `forma_uchovani` z odvozeného listu `Trvanlive_1m_plus`

To je praktické pro současný prototyp, ale není to ještě plně redakčně explicitní model.

## Auditní poznámka

Heuristika byla v dubnu 2026 zpřesněná tak, aby se metody nechytaly falešně jen kvůli substringům uvnitř jiných slov.

Praktický příklad:

- `želé` už se nově nechytá uvnitř slova `zelenina`

Vedle toho přibyla i odvozená sběrná vrstva:

- `sber_doporuceni` je záměrně opatrné a praktické
- používá obecné zásady sběru a hygieny, ale nepřidává neověřené druhově specifické limity

Stejně opatrně je napsaná i nová vrstva látek a přínosů:

- nepředstírá klinickou jistotu tam, kde není
- u necíleně kurátorských položek může nabídnout přínosový text i bez chemického pole
- use-level chemie se po auditním zpřesnění raději nechává prázdná tam, kde by šlo jen o nepřesný plant-level přenos na jinou část rostliny

## Jak dataset znovu vytvořit

```powershell
python .\scripts\build_v7_canonical.py
```

## Jak se dnes používá

Kanonický dataset už není jen mezikrok:

- je zdrojem pro SQLite
- je zdrojem pro lokální appku
- je vhodný pro export, sdílení a další modelování

## Další nejlepší krok

Nejsilnější další zlepšení by bylo:

- přidat do workbooku explicitní pole pro `sber_doporuceni`, pokud se z odvozené vrstvy stane redakčně důležitý výstup
- a zároveň jednou přidat i explicitní vícenásobné pole pro metody dlouhodobého zpracování, aby tahle vrstva nemusela spoléhat hlavně na heuristické odvozování z volného textu
