# Analýza A Audit Projektu

Audit byl znovu proveden 6. dubna 2026 a tentokrát se soustředil primárně na dvě vrstvy:

- dokumentaci
- data, hlavně na přesnost, stručnost, duplicitu a riziko halucinací

## Shrnutí

Projekt je strukturálně silný, ale potřeboval zpřesnit dvě věci:

- oddělit aktuální referenční dokumentaci od historických snapshotů
- zpřísnit use-level vrstvu `aktivni_latky_text` a `latky_a_logika_text`, aby se do konkrétního použití nepropisovaly informace platné jen pro jinou část téže rostliny

Po auditní opravě dnes platí:

- `117` rostlin
- `273` použití
- `91` trvanlivých forem
- `109` zdrojů
- `0` použití bez zdroje
- `212` použití jen s jedním zdrojem
- `82` použití s explicitním use-level `aktivni_latky_text`
- `54` použití s explicitním use-level `latky_a_logika_text`
- `180` použití má `hlavni_prinos_text` jen jako odvozený fallback z existujícího popisu použití
- `2` zdroje zůstávají nepoužité

Největší aktuální riziko už není rozpad dat. Je to spíš sémantická přesnost:

- část dokumentace dřív vypadala jako aktuální reference, i když šlo jen o historický snapshot
- část use-level chemických polí byla příliš “na úrovni celé rostliny”, ne na úrovni konkrétní použité části

## Metoda auditu

Audit kombinoval:

- ruční revizi hlavních `.md` souborů
- strojové kontroly nad SQLite vrstvou a canonical JSON
- kontroly úplnosti, redundance a vazeb mezi tabulkami
- cílené spot-checky rizikovějších tvrzení a léčivějších profilů proti externím zdrojům

Interně byly zkontrolované hlavně:

- úplnost základních polí u všech `273` použití
- vazby `uses -> use_sources`
- pokrytí `processing_methods`
- use-level vrstva `hlavni_prinos_text`, `aktivni_latky_text`, `latky_a_logika_text`
- překryv `hlavni_prinos_text` vs. `cilovy_efekt`
- dokumentační drift v root `.md` souborech

Externě byly jako sanity check použité hlavně:

- oficiální evropské bylinné monografie EMA tam, kde existují
- původní kurátorské zdroje v datasetu
- u niche a ultra-niche potravních položek zejména PFAF a několik doplňkových extension / technických materiálů

Audit neznamená, že každé jednotlivé tvrzení z `273` použití bylo ručně znovu ověřeno proti internetu. Znamená ale, že byla zkontrolovaná celá datová struktura, všechna pole a nejrizikovější vrstvy tvrzení.

## Audit Dokumentace

### Co je dnes aktuální reference

Tyhle soubory mají být brané jako hlavní aktuální dokumentace:

- `README.md`
- `EXPORTY_A_NORMALIZACE.md`
- `V7_KANONICKY_DATASET.md`
- `SQLITE_DATASET.md`
- `LOKALNI_KATALOG_APLIKACE.md`
- `SEZONNI_VYCHOZI_REZIM_A_SBER.md`
- `LATKY_A_PRINOSY_VRSTA.md`
- `METODY_DLOUHODOBEHO_ZPRACOVANI.md`
- `app/media/README.md`

### Co jsou historické snapshoty

Tyhle soubory nejsou zbytečné, ale nemají se číst jako aktuální stav projektu:

- `ANALYZA_DATASETU.md`
- `AUDIT_DATASETU.md`
- `BRAINSTORM_VYUZITI_A_ZLEPSENI.md`
- `DUBNOVE_ROZSIRENI_A_FOTOZDROJE.md`
- `JARNI_ROZSIRENI_BREZEN_A_KVETEN.md`
- `MEDIA_POKRYTI_A_AUTO_COVERS.md`
- `MEDIA_NAHRADY_PRIORITIZACE.md`
- `WEB_FUNCTIONALITY_AUDIT.md`
- `V7_SCHEMA_NAVRH.md`

Tyhle soubory mají hodnotu jako:

- záznam vývoje
- rozhodovací historie
- návrhový kontext

Nemají ale být primární opora pro dnešní čísla ani dnešní datový model.

### Co bylo zastaralé nebo matoucí

Audit našel hlavně tyto problémy:

- staré počty v některých current-sounding dokumentech
- staré snapshoty, které neměly hned nahoře vysvětlené, že jsou historické
- média byla v některých textech popsaná pro starší stav `105` rostlin
- starší audit projektu pořád mluvil o době, kdy ještě nebyly plné reálné fotky ani jarní březnově-květnové rozšíření

### Verdikt k nadbytečnosti

Na rootu je dokumentů hodně, ale většina není čistě nadbytečná. Problém nebyl v samotné existenci souborů, ale v tom, že nebylo dost jasně řečeno, které jsou:

- aktuální reference
- generované reporty
- historické snapshoty

Jinými slovy: spíš než mazat je správný krok lépe je označit.

## Audit Dat

### Co dopadlo dobře

Strukturálně jsou data ve velmi dobrém stavu:

- `0` použití bez zdroje
- `0` použití bez `zpusob_pripravy`
- `0` použití bez `cilovy_efekt`
- `0` použití bez `hlavni_prinos_text`
- `0` použití bez `sber_doporuceni`
- `0` rostlin bez primární fotky
- `2` nepoužité zdroje, tedy jen nízký redakční dluh

To znamená, že hlavní slabina dnes není chybějící základní struktura, ale přesnost některých odvozených vrstev.

### Největší datový nález

Nejvýznamnější nález auditu byl v nové vrstvě `aktivni_latky_text` a `latky_a_logika_text`.

Původně se use-level chemický kontext u kurátorských profilů přebíral z profilu celé rostliny. To vedlo k tomu, že některá konkrétní použití ukazovala látky nebo logiku, které sice pro danou rostlinu obecně dávají smysl, ale ne pro právě použitou část.

Typické příklady před opravou:

- květ bezu ukazoval i anthokyany a pektiny typické spíš pro plody
- list břízy ukazoval i mízu a betulin z kůry
- list maliníku ukazoval i anthokyany z plodů
- palivové použití borovice a smrku ukazovalo vitamin C z mladých výhonků

To nebyla čistá halucinace, ale byla to zavádějící use-level interpretace.

### Co bylo opraveno

Při auditu byla zpřísněná logika v `scripts/functional_context.py`:

- use-level `aktivni_latky_text` se nově filtruje podle použité části rostliny
- use-level `aktivni_latky_text` se u `palivo` nevyplňuje
- pokud je use-level chemie poctivě nejasná, pole se raději nechá prázdné
- spolu s tím se use-level `latky_a_logika_text` vypíná tam, kde by po ořezu zůstala polopravda

Praktický dopad:

- explicitní use-level chemie klesla z `93` na `82` použití
- `11` původně kurátorských použití bylo záměrně vráceno do prázdného stavu, protože přesný use-level chemický výklad nebyl dost bezpečný
- use-level `latky_a_logika_text` zůstává jen u `54` použití; u zbytku bylo raději ztišeno než přehnaně zobecněno
- `0` palivových použití teď neukazuje zavádějící chemii

To je záměrné zlepšení kvality. Nižší pokrytí je tady lepší než chybná jistota.

### Co zůstává slabé

#### 1. Jednozdrojové použití

`212 / 273` použití má právě jeden zdroj.

To neznamená automaticky chybu. Znamená to ale:

- slabší triangulaci
- vyšší citlivost na chybné čtení zdroje
- vyšší potřebu kurátorské opatrnosti u niche a ultra-niche položek

#### 2. Redundance `hlavni_prinos_text`

`180` použití má `hlavni_prinos_text` fakticky shodné s `cilovy_efekt`.

To není halucinace, ale je to slabší informační návrh. Pole sice není prázdné, ale nepřináší nový úhel pohledu.

#### 3. Chybějící use-level chemie

Po zpřísnění je dnes bez explicitního `aktivni_latky_text` `191` použití.

To je současně:

- nedostatek pokrytí
- ale i důkaz, že audit raději odstranil nejistá tvrzení než aby je nechal žít dál

#### 4. Niche jarní vlna

Nejvyšší kurátorské riziko dál leží v okrajových jarních položkách, hlavně tam, kde se opírají o:

- jediný zdroj
- regionální nebo etnobotanicky okrajové zmínky
- druhy s vyšší mírou záměny, toxicity nebo fototoxicity

Typicky:

- `podběl`
- `trnovník akát`
- `bolševník obecný`
- některé ultra-niche listové druhy z dubnové a květnové vlny

Tyhle řádky nejsou nutně špatně. Jen mají nižší důkazní komfort než mainstreamové položky.

## Posouzení Rizika Halucinací

### Co dnes působí bezpečně

Relativně bezpečné jsou:

- základní relační struktura dat
- vazby na zdroje
- pole typu `zpusob_pripravy`, `hlavni_rizika`, `legalita_poznamka_cr`
- use-level chemie tam, kde zůstala i po zpřísnění
- mainstreamové léčivější profily, které mají oporu v oficiálních monografiích nebo silné tradiční literatuře

### Kde je riziko vyšší

Vyšší riziko není v “vymyšlených latinských názvech” nebo strukturálním chaosu. Je spíš v těchto situacích:

- use stojí jen na jednom zdroji
- jde o okrajový spring-foraging claim
- profil spojuje více částí jedné rostliny, ale use je jen jedna z nich
- tvrzení je tradiční, ale ne monograficky silné

### Praktický závěr k halucinacím

V datech jsem nenašel známku masivních vymyšlených tvrzení. Našel jsem ale případy, kde tvrzení byla příliš široce přenesena z úrovně celé rostliny na úroveň konkrétního použití. To je přesně ten typ chyby, který je potřeba hlídat, i když nejde o klasickou LLM halucinaci.

## Co ještě chybí

Z pohledu ideální databáze dnes nejvíc chybí:

- explicitní use-level `aktivni_latky_text` pro další bezpečné potravní a pitné položky
- explicitní use-level `latky_a_logika_text`
- méně redundantní `hlavni_prinos_text`
- silnější druhý zdroj u části niche záznamů
- jasnější rozlišení “ověřenější use-level chemie” vs. “jen plant-level obecný profil”

## Doporučené další kroky

### Priorita A: Přesnost dat

1. Ručně rozšířit use-level `aktivni_latky_text` pro nejčastěji zobrazované pitné a léčivé položky.
2. U dalších řádků raději zůstat prázdný než psát plant-level chemii tam, kde nevíme přesnou část.
3. Postupně snížit počet jednozdrojových niche položek u rizikovějších druhů.

### Priorita B: Čistota modelu

1. Oddělit plant-level funkční profil od use-level funkčního profilu ještě explicitněji.
2. Přestat používat `hlavni_prinos_text` jen jako kopii `cilovy_efekt`.
3. Zvážit explicitní pole typu `funkcni_kontext_uroven = plant/use`.

### Priorita C: Dokumentace

1. Držet `README.md` jako rozcestník, ne jako další historický report.
2. Historické snapshoty vždy označit už v prvním odstavci.
3. Generované reporty nebrat jako stabilní reference.

## Celkový verdikt

Projekt je datově i architektonicky silný. Audit ale ukázal důležitou hranici:

- struktura je už velmi dobrá
- nejcennější další práce není nová infrastruktura
- je to redakční zpřesňování významu jednotlivých polí

Po této auditní vlně je projekt přesnější než předtím, hlavně tím, že raději přizná nevyplněné nebo ne zcela use-level pole, než aby tvářil jistotu tam, kde ji zatím nemá.
