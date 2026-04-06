# Audit datasetu českých rostlin

Historická poznámka:
tenhle soubor auditoval původní workbookový stav před pozdějšími jarními rozšířeními, SQLite vrstvou, veřejným webem a novou vrstvou `látky a přínosy`. Pro aktuální stav používej `ANALYZA_A_AUDIT_PROJEKTU.md`.

## Rozsah a metoda

Tento audit je založený na struktuře a obsahu workbooku `cz_rostliny_rozsireny_dataset_v6_jadro_bezne_trvanlive.xlsx`. Kontroloval jsem:

- vnitřní integritu listů
- úplnost a konzistenci klíčových polí
- návaznost odvozených listů na hlavní dataset
- zdrojové vazby
- míru normalizace a filtrovatelnosti
- zjevné redakční nebo copy-paste chyby

Audit neověřuje externě pravdivost jednotlivých botanických tvrzení ani dostupnost URL na internetu. Hodnotí hlavně datový model, kvalitu kurátorské práce a připravenost datasetu pro další použití.

## Celkový verdikt

Workbook je obsahově silný a strukturálně překvapivě čistý. Největší problém není rozpad dat, ale to, že část schématu je pořád více „kurátorský zápisník“ než plně normalizovaná databáze.

Jinými slovy:

- pro člověka je workbook užitečný a dobře čitelný
- pro filtrování, analytiku a budoucí aplikace bude potřebovat ještě jednu vrstvu standardizace

## Co prošlo velmi dobře

- `record_id` jsou unikátní, souvislá a bez mezer od `R001` do `R237`.
- V `Starter_dataset` nejsou prázdné hodnoty v hlavních povinných sloupcích.
- Nebyly nalezeny duplicity `record_id`.
- Nebyly nalezeny duplicitní řádky ani duplicitní kombinace `vedecky_nazev + cast_rostliny + domena + poddomena`.
- `Trvanlive_1m_plus` i `Jadro_bezne_1m_plus` obsahují pouze existující `record_id` z hlavního listu.
- Sdílené sloupce v odvozených listech odpovídají hlavnímu listu přesně, bez rozjetých kopií.
- Všechny odkazované zdroje existují v listu `Zdroje`.
- V listu `Zdroje` nechybí URL.
- Bezpečnostní a právní pole jsou vyplněná výrazně lépe než u běžných hobby datasetů.

To je velmi dobrý základ.

## Hlavní nálezy

### 1. Vysoká priorita: taxonomie je jen částečně normalizovaná

Největší strukturální slabina workbooku je míchání řízených kategorií a volného textu v jednom sloupci.

Nejvýraznější příklady:

- `poddomena`: 210 unikátních hodnot na 237 řádků
- `cast_rostliny`: 60 unikátních hodnot na 237 řádků
- `status_v_CR`: 45 variant

To znamená, že některé sloupce fungují spíš jako mikropopisy než jako stabilní číselník.

Praktický dopad:

- hůř se filtruje
- hůř se dělá faceted search
- hůř se agreguje po kategoriích
- zvyšuje se riziko téměř-duplicit
- budoucí rozšiřování bude vytvářet další varianty téhož

Konkrétní příklady nejednotnosti:

- `květ` vs `květy`
- `list` vs `listy` vs `mladé listy` vs `čerstvý list`
- `původní, běžný` vs `původní, běžná` vs `původní, běžné`

To není chyba obsahu, ale chyba úrovně normalizace.

### 2. Střední priorita: dokumentace nepokrývá celý workbook

`Slovnik_sloupcu` dobře dokumentuje `Starter_dataset`, ale nepokrývá speciální pole z ostatních listů.

Nedokumentovaná pole:

- v `Zdroje`: `zdroj_id`, `nazev`, `url`
- v `Trvanlive_1m_plus`: `forma_uchovani`, `orientacni_trvanlivost`, `poznamka_k_skladovani`
- v `Jadro_bezne_1m_plus`: `forma_uchovani`, `orientacni_trvanlivost`, `proc_je_v_jadru`

Praktický dopad:

- nový uživatel workbooku musí význam části sloupců odhadovat
- pro export do webu nebo API chybí oficiální definice polí
- obtížněji se nastaví validační pravidla

### 3. Střední priorita: důkaznost je užitečná, ale audit trail je u slabších položek tenký

Silná stránka workbooku je, že má `dukaznost_typ` i `dukaznost_skore`. Slabší stránka je nerovnoměrnost sekundární opory.

Zjištění:

- `zdroj_id_2` chybí u 75,1 % hlavních záznamů
- všech 7 položek se skóre `E` má jen jeden explicitní zdroj
- u `D` položek má druhý zdroj jen 4 z 32 záznamů
- dva konkrétní zdroje `S01` a `S30` jsou použity po 40 záznamech
- zdrojová báze je silně opřená o `PFAF` a `EMA`

To neznamená, že obsah je slabý. Znamená to, že pro auditovatelnou databázi by bylo dobré:

- posílit sekundární zdroje u `D` a `E`
- více odlišit primární, sekundární a inspirační zdroje
- zavést stav typu `ověřeno`, `čeká na ověření`, `analog`, `folklór`

### 4. Střední priorita: hodnoty „neaplikovatelné“ nejsou zapisované konzistentně

U sloupce `palivovy_potencial` se používají dvě strategie:

- explicitní hodnota `neaplikovatelné`
- prázdná buňka

Rozptyl je poměrně velký:

- 184 řádků mají `neaplikovatelné`
- 46 řádků je prázdných

Praktický dopad:

- dotazy nad daty musí ošetřovat dvě reprezentace téže logiky
- exporty a filtry budou dávat nečisté výsledky

Toto je ideální kandidát na jednoduchou standardizaci.

### 5. Nízká až střední priorita: v jádrovém shortlistu jsou redakční nesrovnalosti

List `Jadro_bezne_1m_plus` je strukturálně v pořádku, ale v poli `proc_je_v_jadru` je několik zjevných textových přešlapů nebo copy-paste stop.

Příklady:

- `R159` `slivoň / švestka domácí` `povidla`: text mluví o „formě šípků“
- `R166` `bez černý` `sušený bezový květ na čaj`: text mluví o „listovém čaji“
- `R179` `jalovec obecný` `sušené jalovčinky jako koření`: text mluví o „lesních čajových drogách“
- `R180` `vrba` `sušená kůra do zásoby na odvar`: text mluví o „trvanlivé vůni“

Nejde o problém datového modelu, ale o signál, že shortlist si zaslouží ještě jednu redakční korekturu.

### 6. Nízká priorita: ve zdrojích jsou dvě nepoužité položky

V listu `Zdroje` zůstaly dvě nepoužité reference:

- `S69` `PFAF: Betula pendula`
- `S77` `PFAF: Pinus sylvestris`

To je drobnost, ale pro čistotu verze je dobré rozhodnout, zda:

- je odstranit
- nebo je začít používat

### 7. Nízká priorita: README obsahuje kategorii, která se v datech zatím nepoužívá

`README` zmiňuje `izolovaný záznam`, ale v `Starter_dataset` se tento status nevyskytuje.

To není problém samo o sobě. Jen je dobré si vyjasnit, zda:

- jde o připravenou budoucí kategorii
- nebo o kategorii, která se nakonec nepoužila

## Co je naopak překvapivě silné

- `hlavni_rizika` jsou vyplněná na 100 % řádků
- `legalita_poznamka_CR` je vyplněná na 100 % řádků
- `fenologicka_faze`, `typicke_lokality_v_CR` a `zpusob_pripravy_nebo_vyuziti` dávají datasetu velmi vysokou praktickou hodnotu
- odvozené listy nejsou rozbité ruční editací
- trvanlivost a „core shortlist“ jsou velmi dobrý produktový nápad, ne jen technický filtr

To jsou důležité plusy, protože většina amatérských datasetů selhává právě na těchto místech.

## Doporučené pořadí oprav

### 1. Rychlé opravy s vysokým efektem

- sjednotit `palivovy_potencial` na jednu reprezentaci `N/A`
- ručně projít `proc_je_v_jadru` a opravit zjevné textové chyby
- rozhodnout o osudu `S69` a `S77`
- doplnit slovník pro speciální pole odvozených listů

### 2. Druhá vlna: lepší strojová použitelnost

- rozdělit `poddomena` na normalizovanou kategorii a volný detail
- zavést číselník pro `cast_rostliny`
- rozdělit `status_v_CR` na více jednoduchých polí, například původnost, pěstovanost, četnost
- zavést jednotná pravidla pro zápis `N/A`, prázdné hodnoty a vícehodnotové kombinace

### 3. Třetí vlna: auditovatelnější znalostní báze

- přidat stav verifikace
- přidat samostatný list nebo tabulku pro synonymii
- přidat více sekundárních zdrojů u `D` a `E`
- oddělit „silně podložené“, „tradiční“, „analogické“ a „kuriozní“ položky do jasnějšího workflow

## Doporučení jednou větou

Nejlepší další krok není přidat další stovky řádků, ale udělat verzi `v7`, která zachová obsah a zlepší schéma, dokumentaci a redakční čistotu. Tím se z velmi dobrého workbooku stane opravdu silná datová báze.
