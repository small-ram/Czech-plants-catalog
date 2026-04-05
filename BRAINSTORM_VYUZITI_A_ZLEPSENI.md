# Brainstorm: využití a zlepšení datasetu

## Na co se tenhle dataset dá použít

### 1. Vyhledávací katalog českých rostlin podle použití

Z workbooku může vzniknout web nebo interní katalog, kde půjde filtrovat podle:

- domény použití
- části rostliny
- sezóny
- lokality
- trvanlivosti
- důkaznosti
- rizik

To je pravděpodobně nejpřirozenější produktová forma.

### 2. Sezónní foraging planner

Dataset už obsahuje `obdobi_ziskani`, `fenologicka_faze` a `typicke_lokality_v_CR`. To je ideální základ pro plánovač typu:

- co teď v ČR dává smysl sbírat
- na co si dát pozor
- co se z toho dá udělat
- co se dá usušit nebo uložit na později

### 3. „Wild pantry“ nebo domácí zásobárna

Trvanlivá vrstva je velmi silná. Dá se použít jako základ pro:

- databázi domácích zásob
- přehled sušení, sirupů, octů a zavařenin
- systém „co si na jaře a v létě připravit na zimu“

To je velmi praktická a dobře komunikovatelná osa projektu.

### 4. Kurátorovaný AI asistent

Workbook má dobrou strukturu pro RAG nebo expertního asistenta. Asistent by mohl odpovídat na dotazy jako:

- jaké běžné české rostliny se dají usušit na čaj
- které plody mají vysokou použitelnost v ČR a dlouhou trvanlivost
- co je vhodné spíš jako folklórní zajímavost než jako doporučení

Silnou výhodou je kombinace:

- použitelnosti
- rizik
- právních poznámek
- důkaznosti

### 5. Obsahový web nebo newsletter

Z jednoho řádku lze dělat:

- článek
- krátké edukativní posty
- sezónní tip týdne
- „zapomenutá rostlina týdne“
- přehledy typu „5 českých rostlin na zimní zásobu“

Dataset má už teď dost bohatý textový materiál na obsahový stroj.

### 6. Výukový materiál pro workshopy

Hodí se pro:

- etnobotanické workshopy
- foraging kurzy
- domácí zpracování rostlin
- aromatické a vykuřovací tradice
- srovnání mainstreamu a zapomenutých použití

### 7. Regionální kulturní a krajinářský projekt

Může vzniknout:

- mapa tradičních využití rostlin v ČR
- digitální herbář zaměřený na praxi
- lokální „kulturní botanika“
- obsah pro muzea, knihovny nebo naučné stezky

### 8. Produktový výzkum

Dataset se dá použít pro hledání nápadů na:

- čajové směsi
- sirupy a cordialy
- octy a bitters
- bylinné směsi
- dárkové sady
- aromatické produkty

Ne nutně pro okamžitý prodej, ale velmi dobře pro ideation a shortlist.

### 9. Výzkumný a kurátorský gap analysis

Protože máš u každé položky důkaznost i zdrojovou oporu, dá se dataset použít na zjištění:

- kde jsou slabě podložené domény
- které taxony mají málo ověřených použití
- kde jsou největší „bílé mapy“ pro další výzkum

### 10. Knowledge graph

Data už se dají převést na graf vztahů:

- rostlina
- část rostliny
- použití
- forma uchování
- sezóna
- riziko
- zdroj

To by otevřelo cestu k pokročilejšímu vyhledávání a doporučování.

### 11. Kniha nebo příručka

Workbook má dobrý základ pro kapitoly typu:

- jarní listy a výhonky
- letní květy a sirupy
- podzimní plody a zavařeniny
- kořeny, kůry a zásoby na zimu
- běžné druhy versus téměř zapomenuté použití

### 12. Hodnoticí systém „nejpraktičtější české rostliny“

Na základě aktuálních sloupců lze vytvořit skórování:

- dostupnost
- důkaznost
- riziko
- trvanlivost
- všestrannost

To by bylo výborné pro shortlisty, doporučení i onboarding uživatelů.

## Co by šlo zlepšit na datové úrovni

### 1. Rozdělit řízené číselníky od volného textu

To je nejdůležitější zlepšení.

Příklad:

- `poddomena_normalized`: čaj, sirup, koření, likér, sušení, odvar
- `poddomena_detail`: jemný lidský popis

Stejně tak u:

- `cast_rostliny`
- `status_v_CR`
- `forma_uchovani`

### 2. Přidat samostatný list pro synonymii

README to ostatně samo navrhuje. To by pomohlo řešit:

- více českých názvů
- agregované taxony typu `Tilia spp.`
- různé latinské varianty nebo aktualizace nomenklatury

### 3. Oddělit `léčba` a `fytoterapie` ještě jasněji

Smysl obou kategorií je v datech vidět, ale bylo by dobré ho formalizovat.

Například přidat pole:

- `rezim_pouziti`: tradiční domácí použití / oficiální bylinný léčivý přípravek / folklór / analog

### 4. Přidat workflow verifikace

Velmi užitečné by bylo:

- `stav_overeni`
- `posledni_revize`
- `revidoval`
- `duvod_skore`

To by z workbooku udělalo silnější kurátorský systém.

### 5. Přidat strukturovanější bezpečnost

Místo jednoho bohatého textu by šlo přidat i pomocná pole:

- `riziko_uroven`
- `kontraindikace_tehotenstvi`
- `interakce_leky`
- `nevhodne_pro_deti`
- `nutna_tepelna_uprava`

Volný text by zůstal, ale přibyla by lepší filtrovatelnost.

### 6. Přidat strojově přívětivou sezónnost

Vedle textu `VI–VII` nebo `IX–XI` by pomohla normalizovaná pole:

- `mesic_od`
- `mesic_do`
- `jaro_leto_podzim_zima`

To by výrazně pomohlo aplikacím a kalendářům.

### 7. Přidat geografii a habitatové tagy

Vedle popisných lokalit by se hodily tagy jako:

- les
- remízek
- mez
- sad
- zahrada
- ruderál
- mokřad
- horská poloha

Tím by se dataset stal mnohem lépe mapovatelný.

### 8. Přidat ekonomiku a praktičnost

Zajímavá budoucí pole:

- `vynosnost`
- `snadnost_sberu`
- `snadnost_zpracovani`
- `potrebne_vybaveni`
- `vhodne_pro_zacatecnika`

To by z datasetu udělalo velmi silný rozhodovací nástroj.

### 9. Přidat multimédia a externí identifikátory

Užitečné by byly:

- fotografie
- ilustrace
- odkazy na herbáře
- GBIF / POWO / Wikidata ID

To pomůže jak validaci, tak budoucímu webu.

### 10. Přidat víceúrovňovou práci se zdroji

Místo dvou sloupců `zdroj_id_1` a `zdroj_id_2` by bylo robustnější mít samostatnou relační tabulku:

- `record_id`
- `zdroj_id`
- `role_zdroje`
- `poznamka_ke_zdroji`

To by odstranilo limit „jen dva zdroje na řádek“.

## Rychlé praktické zlepšováky pro další verzi

- opravit textové přešlapy v `Jadro_bezne_1m_plus`
- doplnit slovník pro odvozené listy
- sjednotit zápis `neaplikovatelné` a prázdných hodnot
- zavést 5 až 15 hlavních normalizovaných kategorií pro `poddomena`
- přidat list `Synonyma`
- přidat pole `stav_overeni`
- doplnit druhý zdroj hlavně u `D` a `E`
- vyexportovat workbook také do `csv` nebo `json`

## Silné produktové směry, které z toho mohou vzniknout

- databáze „Co jde v ČR sbírat a zpracovat“
- český wild pantry průvodce
- etnobotanický obsahový web
- AI asistent nad českými rostlinami
- edukační kurz nebo workshopová osnova
- výzkumná mapa zapomenutých použití
- systém doporučení „co sbírat právě teď“

## Doporučení, kam bych šel dál

Kdybych měl vybrat nejrozumnější další krok, šel bych touto cestou:

- zachovat stávající obsah
- udělat lehkou normalizační vrstvu
- opravit redakční detaily
- připravit export pro web nebo aplikaci

Obsahová hodnota datasetu je už teď vysoká. Největší násobič další kvality je teď datový design, ne jen další ruční přidávání nových rostlin.
