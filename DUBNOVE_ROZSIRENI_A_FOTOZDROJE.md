# Dubnové Rozšíření A Fotozdroje

## Co se změnilo

Na začátku dubna 2026 se projekt rozšířil ve třech směrech:

- první kurátorská vlna přidala použitelné jarní položky jako `buk`, `hloh`, `řeřišnice luční` a `pažitka`
- druhá vlna šla více do niche vrstvy a doplnila `lípu`, `plicník`, `řeřišničník chlupatý`, `rozrazil potoční`, `kerblík lesní`, `jilm horský` a `rukevník východní`
- třetí, ultra-niche vlna přidala ještě nenápadnější dubnové druhy z ruderálních míst, zahradních přechodů a okrajových etnobotanických zmínek

Současně katalog přešel od částečné foto vrstvy k plnému pokrytí skutečnými Wikimedia fotkami.

## Nové zdroje

Do sheetu `Zdroje` přibyly:

- `S79` `PFAF: Fagus sylvatica`
- `S80` `PFAF: Crataegus monogyna`
- `S81` `PFAF: Cardamine pratensis`
- `S82` `PFAF: Allium schoenoprasum`
- `S83` `PFAF: Tilia cordata`
- `S84` `PFAF: Pulmonaria officinalis`
- `S85` `PFAF: Cardamine hirsuta`
- `S86` `PFAF: Veronica beccabunga`
- `S87` `PFAF: Anthriscus sylvestris`
- `S88` `PFAF: Ulmus`
- `S89` `PFAF: Bunias orientalis`
- `S90` `PFAF: Lapsana communis`
- `S91` `PFAF: Barbarea vulgaris`
- `S92` `PFAF: Hesperis matronalis`
- `S93` `PFAF: Campanula rapunculoides`
- `S94` `PFAF: Lepidium campestre`
- `S95` `PFAF: Campanula trachelium`

## Nové dubnové záznamy

Do `Starter_dataset` přibyly:

- `R238` `buk lesní` — `mladé bukové listy do salátu`
- `R239` `hloh obecný / jednosemenný` — `mladé listy a výhonky do salátu`
- `R240` `hloh obecný / jednosemenný` — `sušené listy na nálev / čajovou náhražku`
- `R241` `řeřišnice luční` — `listy a květy do jarního salátu`
- `R242` `pažitka pobřežní` — `čerstvá nať / sušení / mražení`
- `R243` `lípa srdčitá / lípa velkolistá` — `mladé listy do salátu / na chléb`
- `R244` `lípa srdčitá / lípa velkolistá` — `jarní míza / odpaření na sirup`
- `R245` `plicník lékařský` — `mladé listy syrové / krátce tepelně upravené`
- `R246` `řeřišničník chlupatý` — `peprná příměs do salátu / na chléb`
- `R247` `rozrazil potoční` — `listy syrové / krátce povařené ve směsi`
- `R248` `kerblík lesní` — `listy syrové / vařené jako jarní bylina`
- `R249` `jilm horský` — `mladé listy syrové / krátce vařené`
- `R250` `rukevník východní` — `mladé listy a lodyhy syrové / vařené`
- `R251` `kapustka obecná` — `mladé listy syrové / vařené`
- `R252` `barborka obecná` — `peprné listy a výhony syrové / vařené`
- `R253` `večernice vonná` — `listy a květy do salátu / jako ozdoba`
- `R254` `zvonek řepkovitý` — `mladé listy a výhony syrové / vařené`
- `R255` `řeřicha rolničková` — `časná peprná brukvovitá zeleň`
- `R256` `zvonek kopřivolistý` — `jarní listy do směsí / krátce vařené`

Do `Trvanlive_1m_plus` přibyly:

- `R240` — `sušení listů na čajovou směs`
- `R242` — `sušení nebo mražení nasekaných listů`
- `R244` — `odpaření mízy na koncentrát / sirup`

## Ultra-Niche Vrstva

Třetí vlna byla záměrně postavená tak, aby šla mimo běžné české jarní seznamy:

- `kapustka obecná`
  nenápadná městská a ruderální listová zelenina
- `barborka obecná`
  ostřejší brukvovitý list a výhon
- `večernice vonná`
  zahradně-zplaňující jedlá brukvovitá rostlina
- `zvonek řepkovitý`
  velmi málo očekávaná listová jedlost
- `řeřicha rolničková`
  suchomilnější peprná dubnová brukvovitá alternativa
- `zvonek kopřivolistý`
  regionálněji doložená, ale velmi okrajová listová jedlost

## Důležité kurátorské poznámky

Nové niche a ultra-niche vlny jsou záměrně pestřejší i riskantnější, takže některé řádky mají silnější varování:

- `R247` `rozrazil potoční`
  hlavní riziko je kontaminace vody, ne záměna
- `R248` `kerblík lesní`
  hlavní riziko je záměna s prudce jedovatými miříkovitými
- `R244` `lípa míza`
  hlavní riziko je poškození stromu a nelegální odběr
- `R250` `rukevník východní`
  jde o nepůvodní zdomácnělý druh, při sběru se nemají roznášet semena
- `R253` `večernice vonná`
  prakticky dává největší smysl ze známých neošetřených výsadeb

## Dopad na data

Aktuální stav po rebuild:

- `105` rostlin
- `256` použití
- `86` trvanlivých forem
- `95` zdrojů
- `86` dubnových použití
- `50` rostlin dostupných v dubnovém filtru

## Fotky z důvěryhodných zdrojů

Media manifest teď obsahuje `105` reálných fotek typu `photo` pro všech `105` rostlin v datasetu.

Použitý workflow:

- ručně kurátorované první batch doplnění
- automatické dohledání přes Wikipedia, Wikidata a Wikimedia Commons
- zápis do `plant_media.json` včetně `source_url`, `credit` a pokud bylo dostupné, i `license`

Výsledek:

- `105/105` rostlin má `primary_photo`
- v galerii už nezůstávají žádné placeholder-only rostliny

## Důležité chování v appce

- API a UI jako hlavní obrázek berou jen `photo`
- detail i exporty ukazují `credit`, `source_name`, `source_url` a pokud je známá, i `license`
- po plném Wikimedia fill už katalog nemá žádnou rostlinu bez skutečné primární fotky

## Reprodukovatelnost

Kurátorský update lze znovu aplikovat skriptem:

```powershell
python .\scripts\curate_april_sources_and_media.py
```

Pak stačí rebuild:

```powershell
python .\scripts\build_all.py
```

A pro doplnění Wikimedia fotek:

```powershell
python .\scripts\fill_wikimedia_photos.py
```
