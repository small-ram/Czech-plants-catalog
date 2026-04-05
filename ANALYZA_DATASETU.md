# Analýza datasetu českých rostlin

## Co tento workbook ve skutečnosti je

Tento `.xlsx` soubor není botanický atlas ani úplný seznam české flóry. Je to kurátorovaná, prakticky orientovaná etnobotanická databáze, která mapuje konkrétní použití rostlin v českém kontextu.

Nejdůležitější princip datového modelu je tento:

- 1 řádek v `Starter_dataset` = 1 konkrétní použití určitého druhu nebo skupiny druhů.

To znamená, že dataset není organizován primárně podle taxonomie, ale podle použití. Stejná rostlina se proto může objevit vícekrát, pokaždé s jinou částí rostliny, jinou doménou použití, jiným efektem, jinou důkazností a jiným rizikovým profilem.

Z hlediska obsahu jde o mix těchto vrstev:

- potrava
- pití
- fytoterapie
- lidové léčebné použití
- vůně a vykuřování
- palivo
- trvanlivé formy uchování

Workbook tedy funguje spíš jako znalostní báze pro praktické využití rostlin než jako klasická botanická tabulka.

## Struktura workbooku

| List | Počet řádků | Role |
|---|---:|---|
| `README` | 14 informačních položek | vysvětluje záměr, metodiku a limity |
| `Slovnik_sloupcu` | 25 definic | vysvětluje hlavní pole `Starter_dataset` |
| `Starter_dataset` | 237 | hlavní tabulka použití |
| `Zdroje` | 78 | katalog zdrojů a URL |
| `Trvanlive_1m_plus` | 83 | podmnožina použití s orientační trvanlivostí 1 měsíc a více |
| `Jadro_bezne_1m_plus` | 60 | ručně kurátorované „nejpraktičtější jádro“ trvanlivých položek |

Prakticky jde o jeden hlavní list a dva odvozené pohledy:

- `Starter_dataset` = kompletní pracovní základ
- `Trvanlive_1m_plus` = filtr na dlouhodobě skladovatelné formy
- `Jadro_bezne_1m_plus` = užší praktický shortlist

## Kvantitativní profil dat

### Rozsah

- 237 záznamů v hlavním datasetu
- 91 vědeckých taxonů nebo taxonomických skupin
- 97 českých názvů
- ID jsou souvislá od `R001` do `R237` bez mezer
- listy `Trvanlive_1m_plus` a `Jadro_bezne_1m_plus` pokrývají blok `R155` až `R237`, tedy zjevně novější tematické rozšíření

### Rozložení podle domény v `Starter_dataset`

- `potrava`: 78 záznamů, 32,9 %
- `pití`: 69 záznamů, 29,1 %
- `potrava a pití`: 32 záznamů, 13,5 %
- `fytoterapie`: 31 záznamů, 13,1 %
- `vůně`: 11 záznamů, 4,6 %
- `léčba`: 9 záznamů, 3,8 %
- `palivo`: 7 záznamů, 3,0 %

Když se domény seskupí do větších bloků, vychází:

- jídlo a pití dohromady: 179 záznamů, 75,5 %
- zdraví, vůně a palivo dohromady: 58 záznamů, 24,5 %

Dataset je tedy primárně praktický a „pantry/foraging“ orientovaný, ne čistě léčivkářský.

### Rozložení podle znalostního statusu

- `mainstream`: 95 záznamů, 40,1 %
- `méně známé`: 93 záznamů, 39,2 %
- `téměř zapomenuté`: 36 záznamů, 15,2 %
- `globální analog`: 13 záznamů, 5,5 %

Interpretace:

- skoro 80 % datasetu tvoří známé nebo reálně použitelné méně známé položky
- zhruba 21 % tvoří kurátorská vrstva „zajímavých okrajů“: zapomenuté a přenesené analogie

To dává workbooku dobrou rovnováhu mezi praktičností a objevností.

### Rozložení podle důkaznosti

- `A`: 41 záznamů, 17,3 %
- `B`: 118 záznamů, 49,8 %
- `C`: 39 záznamů, 16,5 %
- `D`: 32 záznamů, 13,5 %
- `E`: 7 záznamů, 3,0 %

To ukazuje, že jádro workbooku stojí hlavně na:

- oficiálních monografiích a silně opřených položkách `A`
- dobře kurátorovaných tradičních a etnobotanických položkách `B`

Slabší, spekulativnější nebo přenesené položky jsou přítomné, ale tvoří menšinu. To je zdravý poměr pro kurátorovaný pracovní dataset.

## Jaké informace dataset zachycuje

Hlavní list kombinuje několik vrstev najednou:

- identitu rostliny
- status v ČR
- použitou část rostliny
- typ použití
- praktické lokality
- sezónní okno sběru
- způsob přípravy
- cílový efekt
- chuť a vůni
- rizika, kontraindikace a legální poznámku
- typ a sílu zdrojové opory

To je silné zejména proto, že nejde jen o „co je jedlé“, ale o celý praktický kontext:

- kde rostlinu v ČR typicky hledat
- kdy ji sbírat
- co z ní dělat
- proč ji dělat
- jaká jsou omezení
- o jak kvalitní znalost se opírá

## Co říká trvanlivá vrstva

`Trvanlive_1m_plus` obsahuje 83 záznamů, tedy 35,0 % hlavního datasetu. Je v něm:

- 47 vědeckých taxonů
- 48 českých názvů

Rozložení podle domény:

- `pití`: 36 záznamů, 43,4 %
- `potrava`: 29 záznamů, 34,9 %
- ostatní domény dohromady: 18 záznamů, 21,7 %

Rozložení podle formy uchování:

- `sušení`: 44 záznamů, 53,0 %
- `sirup / koncentrát`: 8 záznamů, 9,6 %
- `zavařenina`: 6 záznamů, 7,2 %
- zbytek tvoří ocet, macerace, pražení, oleje, skladování ve skořápce, pryskyřice a další specializované formy

To ukazuje, že rozšíření je postaveno hlavně kolem:

- sušených čajů, listů, květů, kořenů a plodů
- domácích sirupů a zavařenin
- dlouhodobě skladovatelných „wild pantry“ položek

## Co říká „jádro běžných položek“

`Jadro_bezne_1m_plus` obsahuje 60 záznamů, tedy 25,3 % hlavního datasetu. Je v něm:

- 41 vědeckých taxonů
- 42 českých názvů

Je to nejpraktičtější shortlist. Oproti širší trvanlivé vrstvě méně zahrnuje kuriozity a více tlačí na:

- běžně dostupné druhy
- vysokou použitelnost
- domácí zpracování bez specializované technologie

I tady dominuje:

- `pití`: 43,3 %
- `potrava`: 36,7 %
- `sušení`: 53,3 % všech forem uchování

Z hlediska budoucího produktu nebo aplikace je to nejsilnější „startovní katalog“.

## Zdrojová základna

- 78 záznamů ve zdrojovém listu
- 76 z nich je skutečně použito
- žádný odkazovaný `zdroj_id` nechybí
- žádný zdroj nemá prázdné URL
- 59 hlavních záznamů má sekundární zdroj `zdroj_id_2`
- 178 záznamů stojí jen na jednom explicitním zdroji

Zdrojová báze se opírá hlavně o:

- `pfaf.org`: 41 zdrojů
- `www.ema.europa.eu`: 21 zdrojů
- menší počet výzkumných článků a etnobotanických studií

Nejpoužívanější konkrétní zdroje jsou:

- `S01`: česká etnobotanická review wild edible plants
- `S30`: etnobotanický survey severozápadního Chorvatska

Oba jsou citované po 40 použitích, což naznačuje silné kurátorské spoléhání na několik „deštníkových“ pramenů.

## Jak tento dataset číst interpretačně

Nejlepší mentální model není „seznam rostlin“, ale:

- databáze použití
- databáze sezónních příležitostí
- databáze tradičního know-how
- databáze praktických domácích forem uchování

Silná stránka workbooku je právě propojení mezi:

- rostlinou
- částí rostliny
- sezónou
- místem výskytu
- účelem
- rizikem
- zdrojem

To z něj dělá vhodný základ pro:

- filtrovací katalog
- obsahový web
- kurátorovaný vyhledávač
- RAG/AI znalostní bázi
- sezónní foraging planner
- domácí „wild pantry“ nebo herbářový projekt

## Největší silné stránky obsahu

- Dataset má jasný účel a metodiku, není to nahodilá sbírka poznámek.
- Bezpečnost, rizika a právní poznámky nejsou přidané okrajově, ale systematicky.
- Evidence není binární; má vlastní typ i skóre.
- Trvanlivé a praktické vrstvy dávají workbooku vysokou použitelnost.
- Odvozené listy jsou konzistentní podmnožiny hlavního datasetu, ne ručně rozpadlé kopie.

## Celkový závěr

Obsahově jde o velmi zajímavý a už dost vyzrálý základ pro českou aplikovanou etnobotaniku. Není to univerzální botanická databáze, ale naopak poměrně dobře vymezený „knowledge system“ pro praktické použití rostlin v českém prostředí.

Největší hodnota workbooku je v tom, že kombinuje:

- praktičnost
- sezónnost
- zdrojovost
- rizikovost
- kulturně-tradiční vrstvu
- trvanlivé domácí zpracování

To je kombinace, která se dá dál velmi dobře rozvíjet jak do lidsky čitelného katalogu, tak do strojově využitelné databáze.
