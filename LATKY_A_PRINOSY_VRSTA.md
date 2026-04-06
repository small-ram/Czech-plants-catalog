# Látky A Přínosy Vrstva

## Co tahle vrstva dělá

Nová vrstva doplňuje k použitím a rostlinám odpověď na otázky:

- proč to vůbec dává smysl
- na co to tradičně míří
- jaké hlavní užitečné nebo aktivní látky v tom hrají roli
- jaká je rozumná logika mezi látkami a praktickým použitím

Nejde o klinickou databázi léčby. Je to opatrná kurátorská a uživatelsky orientovaná vrstva mezi syrovým popisem použití a praktickým rozhodováním v katalogu.

## Aktuální pokrytí

Stav po rebuild k `2026-04-06`:

- `117` rostlin celkem
- `273` použití celkem
- `26` rostlin má kurátorský funkční profil
- `26` rostlin má explicitní pole `aktivni_latky_text`
- `273` použití má pole `hlavni_prinos_text`
- `93` použití má explicitní pole `aktivni_latky_text`
- `93` použití je označeno jako `kuratorsky_profil`
- `180` použití je označeno jako `odvozeno_z_pouziti`

Prakticky to znamená:

- u vybraných pitných a léčivěji orientovaných rostlin je k dispozici ručně kurátorské shrnutí přínosu i látek
- u zbytku použití je aspoň odvozené shrnutí typu „proč to může dávat smysl“, aby detail nezůstal prázdný

## Nová pole

Na úrovni `uses`:

- `hlavni_prinos_text`
  stručné vysvětlení, proč je dané použití prakticky zajímavé
- `aktivni_latky_text`
  hlavní užitečné nebo aktivní látky či skupiny látek, pokud jsou kurátorsky doplněné
- `latky_a_logika_text`
  opatrné propojení mezi látkami, chutí, aromatem a tradičním účelem
- `funkcni_kontext_status`
  původ funkční vrstvy

Na úrovni `plants`:

- `hlavni_prinos_text`
- `aktivni_latky_text`
- `latky_a_logika_text`
- `funkcni_kontext_status`

## Jak se to dnes tvoří

Vrstva je záměrně hybridní:

- `kuratorsky_profil`
  ručně napsaný profil pro vybranou rostlinu, hlavně tam, kde je prakticky důležité vysvětlit pití, léčivější použití nebo tradiční podpůrnou logiku
- `odvozeno_z_pouziti`
  fallback shrnutí složené z existujících polí jako `domena`, `poddomena`, `zpusob_pripravy_nebo_vyuziti` a `cilovy_efekt`

To je dobrý kompromis:

- uživatel téměř vždy dostane aspoň stručné „proč“
- zároveň se nehalucinuje konkrétní chemie tam, kde zatím nebyla kurátorsky doplněná

## Jak to číst správně

### `hlavni_prinos_text`

Tohle je hlavně uživatelská vrstva. Má rychle odpovědět:

- proč bych to měl zvažovat
- co je na tom prakticky zajímavé
- jestli jde spíš o chuť, aromatiku, slizy, hořčiny, respirační tradici, trávení nebo jiný typ přínosu

### `cilovy_efekt`

Tohle zůstává užší use-level pole:

- na co dané konkrétní použití tradičně míří
- co od něj lidé typicky čekají

### `aktivni_latky_text`

Tohle není laboratorní rozbor. Je to konzervativní přehled hlavních tříd látek, které jsou pro danou rostlinu nebo použití relevantní:

- flavonoidy
- slizy
- třísloviny
- silice
- organosirné látky
- anthokyany
- hořčiny
- salicylátové deriváty

### `latky_a_logika_text`

Tohle pole propojuje chemii a uživatelský smysl:

- proč to chutná nebo voní právě tak
- proč se to tradičně používá právě tímto směrem
- kde je rozumné držet se při zemi a nečíst z látkového profilu víc, než opravdu unese

## Kde se to ukazuje

Vrstva se dnes propisuje do:

- SQLite databáze
- `/api/search`
- `/api/use`
- `/api/plant`
- Markdown exportů `use` a `plant`
- lokální appky
- veřejného GitHub Pages webu

Vyhledávání nově funguje i přes texty přínosů a látek, takže lze najít položky třeba přes:

- `flavonoidy`
- `slizy`
- `trávení`
- `dýchací cesty`
- `uklidnění`

## Omezení a auditní poznámka

Je důležité držet se těchto hranic:

- nejde o lékařské doporučení
- nejde o databázi dávkování
- nejde o náhradu léčby ani diagnostiky
- výslovně se nepředstírá, že každé tradiční použití má stejně silnou evidenci

Současná vrstva je záměrně opatrná:

- tam, kde není kurátorsky jisté látkové vysvětlení, zůstává `aktivni_latky_text` prázdné
- benefitní text může existovat i bez chemického pole
- formulace jsou psané jako tradiční nebo praktický kontext, ne jako tvrdé klinické claimy

## Další nejlepší krok

Nejvyšší další hodnota bude v tomhle pořadí:

- přesunout nejdůležitější funkční profily z kódu do explicitního redakčního pole ve workbooku
- doplnit k profilům samostatné zdrojové reference na úrovni jednotlivých rostlin nebo použití
- rozšířit kurátorské profily z dnešních `26` rostlin na další pitné, léčivé a aromatické druhy
