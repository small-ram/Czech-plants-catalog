from __future__ import annotations

from typing import Any


PLANT_FUNCTIONAL_PROFILES: dict[str, dict[str, str]] = {
    "Sambucus nigra": {
        "aktivni_latky_text": "flavonoidy a fenolické kyseliny v květech, anthokyany a další polyfenoly v plodech, pektiny, aromatické látky",
        "obecny_prinos_text": "Dává smysl hlavně jako aromatická květní rostlina pro nápoje a jako tmavě polyfenolová plodová surovina po tepelné úpravě.",
        "pitny_prinos_text": "K pití dává smysl kvůli voňavým květům a později i kvůli tmavým plodům, které po tepelné úpravě přidávají chuť, barvu a polyfenoly.",
        "lecivy_prinos_text": "V tradičním bylinném použití míří hlavně na horní dýchací cesty, pocení při nachlazení a jemnou podporu sliznic.",
        "latky_a_logika_text": "Smysl dávají hlavně polyfenoly, květní aromatika a pektiny; u plodů je důležitá tepelná úprava a nejde o náhradu léčby.",
    },
    "Pinus sylvestris": {
        "aktivni_latky_text": "monoterpeny a další silice, pryskyřičné látky, polyfenoly, u mladých výhonků i vitamin C",
        "obecny_prinos_text": "Největší hodnotu má jako výrazně aromatická jarní a zimní surovina do nálevů, sirupů a domácích inhalativně působících směsí.",
        "pitny_prinos_text": "Pít to dává smysl hlavně kvůli pryskyřičně lesní vůni, sezónní svěžesti a tradičnímu spojení s dýchacími cestami.",
        "lecivy_prinos_text": "Tradičně se používá hlavně při zahlenění, podrážděných horních dýchacích cestách a tam, kde pomáhá aromatický horký nápoj.",
        "latky_a_logika_text": "Logika stojí hlavně na těkavých terpenických látkách a pryskyřici, které dělají chuť i aromatický respirační efekt.",
    },
    "Betula pendula / Betula pubescens": {
        "aktivni_latky_text": "jednoduché cukry a minerály v míze, flavonoidy a fenolické látky v listech, triterpeny typu betulinu hlavně v kůře",
        "obecny_prinos_text": "Hodí se jako jemná jarní míza a jako lehce svíravá listová čajová nebo podpůrná surovina.",
        "pitny_prinos_text": "Pít to dává smysl hlavně jako velmi lehký jarní nápoj z mízy nebo jako decentní listový nálev.",
        "lecivy_prinos_text": "V tradičním použití míří hlavně na mírnou močovou podporu, jarní 'odlehčení' a lehké čajové směsi.",
        "latky_a_logika_text": "U mízy je logika hlavně v cukrech, minerálech a organických kyselinách; u listů spíš ve flavonoidech a lehce močovém tradičním profilu.",
    },
    "Allium cepa": {
        "aktivni_latky_text": "sirné sloučeniny typu cysteinových sulfoxidů, flavonoidy včetně quercetinu, fenolické látky",
        "obecny_prinos_text": "Smysl má hlavně jako chuťově aktivní kuchyňská a sirupová surovina s tradičním respiračním využitím.",
        "pitny_prinos_text": "V pitné nebo sirupové podobě dává smysl hlavně tam, kde chceš štiplavě sladký domácí prostředek na dýchací cesty.",
        "lecivy_prinos_text": "Tradičně se míří hlavně na zahlenění, kašel a pocit 'rozehřátí' při nachlazení.",
        "latky_a_logika_text": "Logika stojí hlavně na sirných sloučeninách a flavonoidech, které dělají cibuli štiplavou, aromatickou a tradičně ceněnou.",
    },
    "Quercus robur / Q. petraea / Q. pubescens": {
        "aktivni_latky_text": "třísloviny včetně ellagitaninů, další polyfenoly, hořčiny",
        "obecny_prinos_text": "Dub má smysl hlavně jako silně svíravá surovina do odvarů, kloktadel nebo na nouzové potravní zpracování žaludů.",
        "pitny_prinos_text": "K pití dává smysl spíš tam, kde chceš svíravý odvar nebo náhražku z pražených žaludů než příjemný běžný nápoj.",
        "lecivy_prinos_text": "Tradičně míří hlavně na svíravé použití při průjmu, kloktání nebo na vnější použití.",
        "latky_a_logika_text": "Tady je klíč v tříslovinách a svíravosti; právě proto je využití specifické a ne pro každodenní pití.",
    },
    "Matricaria recutita": {
        "aktivni_latky_text": "apigenin a další flavonoidy, silice s bisabololem, matricin/chamazulenové prekurzory, kumariny",
        "obecny_prinos_text": "Je to univerzální jemná květní bylinka pro pití, inhalaci a zklidňující tradiční použití.",
        "pitny_prinos_text": "Pít ho má smysl hlavně jako jemný, uklidňující a chuťově přístupný čaj do večera, při podráždění nebo do směsí.",
        "lecivy_prinos_text": "Tradičně se používá hlavně na trávení, křeče, podráždění sliznic a lehké zklidnění.",
        "latky_a_logika_text": "Logika stojí na kombinaci silic a flavonoidů, které dělají heřmánek aromatický, jemný a tradičně velmi univerzální.",
    },
    "Crataegus monogyna Jacq. / C. laevigata (Poir.) DC.": {
        "aktivni_latky_text": "flavonoidy, oligomerní procyanidiny, fenolické kyseliny",
        "obecny_prinos_text": "Hloh dává smysl hlavně jako jemná listová a květní/čajová rostlina s tradičním kardiálním profilem.",
        "pitny_prinos_text": "Pít ho má smysl hlavně jako jemnější listový nebo květní nálev, když chceš decentní bylinnou podporu a ne silný chuťový zážitek.",
        "lecivy_prinos_text": "Tradičně míří hlavně na srdce, oběh, napětí a dlouhodobé jemné podpůrné užívání.",
        "latky_a_logika_text": "Logika je hlavně ve flavonoidech a procyanidinech; jde ale o podpůrnou bylinu, ne o řešení akutních kardiálních potíží.",
    },
    "Juniperus communis": {
        "aktivni_latky_text": "silice a terpeny, pryskyřičné a hořké látky, flavonoidy",
        "obecny_prinos_text": "Hodí se hlavně jako silně aromatické koření, macerátová složka a digestivně laděný nápojový detail.",
        "pitny_prinos_text": "Pít nebo macerovat ho má smysl hlavně kvůli pryskyřičně kořenité vůni a digestivnímu charakteru.",
        "lecivy_prinos_text": "Tradičně míří hlavně na trávení, lehkou močovou podporu a zahřívací směsi.",
        "latky_a_logika_text": "Hlavní roli hrají silice a terpeny; právě proto je jalovec aromatický, ale také není vhodný ve velkých dávkách ani dlouhodobě.",
    },
    "Abies alba": {
        "aktivni_latky_text": "monoterpeny a další silice, pryskyřice, polyfenoly, u mladých výhonků i vitamin C",
        "obecny_prinos_text": "Jedle dává smysl hlavně jako lesně aromatická surovina do sirupů, nálevů a podpůrných zimních směsí.",
        "pitny_prinos_text": "Pít ji má smysl hlavně kvůli čistě jehličnaté vůni, svěžesti a tradičnímu zimnímu respiračnímu použití.",
        "lecivy_prinos_text": "Tradičně se používá hlavně při kašli, zahlenění a jako aromatická součást dýchacích směsí.",
        "latky_a_logika_text": "Logika stojí hlavně na silicích a pryskyřici, které vytvářejí jehličnaté aroma a tradiční spojení s dýchacími cestami.",
    },
    "Plantago lanceolata": {
        "aktivni_latky_text": "slizy, iridoidní glykosidy typu aucubinu a katalpolu, třísloviny, flavonoidy",
        "obecny_prinos_text": "Jitrocel je silný hlavně jako slizová a jemně svíravá listová bylina pro čaje a sirupy.",
        "pitny_prinos_text": "Pít ho dává smysl hlavně tehdy, když chceš jemný slizový čaj nebo sirup na podrážděný krk a kašel.",
        "lecivy_prinos_text": "Tradičně míří hlavně na suchý kašel, podrážděné sliznice, krk a lehčí zánětlivé stavy dutiny ústní.",
        "latky_a_logika_text": "Smysl dávají slizy, iridoidy a třísloviny; dohromady vysvětlují proč jitrocel působí zklidňujícím a lehce svíravým dojmem.",
    },
    "Carum carvi": {
        "aktivni_latky_text": "silice s karvonem a limonenem, hořké a aromatické látky",
        "obecny_prinos_text": "Kmín má hodnotu hlavně jako trávicí koření a jako čajový detail tam, kde je cílem práce s nadýmáním a těžkým jídlem.",
        "pitny_prinos_text": "Pít ho má smysl hlavně při těžkém trávení, nadýmání a tam, kde nechceš silný léčivý čaj, ale jednoduchý funkční nálev.",
        "lecivy_prinos_text": "Tradičně se používá hlavně na nadýmání, křeče a těžší trávení.",
        "latky_a_logika_text": "Hlavní logika je v silicích, zejména karvonu a limonenu, které nesou aroma i tradiční carminativní charakter.",
    },
    "Armoracia rusticana": {
        "aktivni_latky_text": "glukosinoláty a z nich vznikající isothiokyanáty, vitamin C, ostré sirné látky",
        "obecny_prinos_text": "Křen je silný hlavně jako ostrá kuchyňská a sirupová surovina, která probere chuť i nos.",
        "pitny_prinos_text": "V pitné nebo sirupové podobě dává smysl hlavně tam, kde chceš štiplavý domácí prostředek na zahlenění a 'pročištění'.",
        "lecivy_prinos_text": "Tradičně míří hlavně na zahlenění, horní dýchací cesty a podporu trávení.",
        "latky_a_logika_text": "Logika stojí hlavně na glukosinolatech a isothiokyanátech, které dělají křen ostrý, aromatický a dráždivě stimulační.",
    },
    "Tilia cordata / Tilia platyphyllos": {
        "aktivni_latky_text": "slizové polysacharidy, flavonoidy, třísloviny, jemné aromatické látky v květech",
        "obecny_prinos_text": "Lípa je jemná květní i listová rostlina, která dává smysl pro zklidňující čaje, slizové směsi a lehké jarní pití.",
        "pitny_prinos_text": "Pít ji má smysl hlavně jako voňavý a uklidňující květní nálev nebo jemně slizový nápoj na krk.",
        "lecivy_prinos_text": "Tradičně míří hlavně na nachlazení, pocení, podrážděný krk a večerní zklidnění.",
        "latky_a_logika_text": "Smysl dávají hlavně slizy, flavonoidy a jemná květní aromatika; právě proto je lípa spíš měkká a zklidňující než tvrdě léčivá.",
    },
    "Rubus idaeus": {
        "aktivni_latky_text": "třísloviny a flavonoidy v listech, anthokyany a aromatické látky v plodech",
        "obecny_prinos_text": "Maliník je cenný jednak chuťově v plodech, jednak jako jemně svíravá listová čajová rostlina.",
        "pitny_prinos_text": "Pít ho má smysl hlavně jako příjemný ovocný nebo listový čaj, když chceš jemnou chuť a lehce svíravý profil.",
        "lecivy_prinos_text": "Tradičně se list používá hlavně jako lehce svíravá a podpůrná bylinka, zejména v ženských směsích nebo při průjmu.",
        "latky_a_logika_text": "List stojí hlavně na tříslovinách a flavonoidech, plod spíš na barvivých a chuťových polyfenolech.",
    },
    "Thymus serpyllum agg.": {
        "aktivni_latky_text": "silice s thymolem a carvacrolem, flavonoidy, hořké látky",
        "obecny_prinos_text": "Mateřídouška má smysl jako silně aromatická čajová, sirupová a kuchyňská bylinka s respiračním a trávicím přesahem.",
        "pitny_prinos_text": "Pít ji dává smysl hlavně kvůli teplému bylinnému aroma a tradičnímu spojení s kašlem, krkem a chladem.",
        "lecivy_prinos_text": "Tradičně míří hlavně na kašel, zahlenění, horní dýchací cesty a lehčí zažívací nepohodu.",
        "latky_a_logika_text": "Klíč je v silicích, hlavně thymolu a carvacrolu, které vysvětlují její výrazné aroma i tradiční použití.",
    },
    "Melissa officinalis": {
        "aktivni_latky_text": "kyselina rozmarýnová, flavonoidy, silice s citralem a citronellalem",
        "obecny_prinos_text": "Meduňka je jemná aromatická bylinka pro pití, klid a žaludek; silná je hlavně ve vůni a snesitelnosti.",
        "pitny_prinos_text": "Pít ji má smysl hlavně jako lehce citrusový čaj na večer, napětí nebo neklidný žaludek.",
        "lecivy_prinos_text": "Tradičně míří hlavně na napětí, lehkou nespavost, stresové trávení a jemné uklidnění.",
        "latky_a_logika_text": "Logika stojí hlavně na rozmarýnové kyselině a jemné citrusové siličné frakci; proto působí měkce a příjemně.",
    },
    "Mentha x piperita": {
        "aktivni_latky_text": "menthol, menthon, další silice, kyselina rozmarýnová, flavonoidy",
        "obecny_prinos_text": "Máta je silná jako osvěžující a přitom funkční nápojová bylina s trávicím přesahem.",
        "pitny_prinos_text": "Pít ji má smysl hlavně pro čistě osvěžující chuť, lehkou úlevu při těžkém břiše a přehledný aromatický profil.",
        "lecivy_prinos_text": "Tradičně míří hlavně na trávení, nadýmání, napětí v břiše a osvěžující pocit v dýchacích cestách.",
        "latky_a_logika_text": "Menthol a další silice nesou jak chuť, tak praktický efekt; právě proto je máta užitečná i tam, kde chceš něco příjemného na pití.",
    },
    "Juglans regia": {
        "aktivni_latky_text": "třísloviny, fenolické látky, juglon a další naphthoquinony hlavně v zelených částech, aromatické hořké složky",
        "obecny_prinos_text": "Ořešák dává smysl hlavně jako silně aromatická a tříslovitá surovina pro maceráty, ořechovku a specifické tradiční použití.",
        "pitny_prinos_text": "Pít ho má smysl hlavně v podobě macerátů nebo ořechovky, kde hraje roli hořká chuť, aroma a třísloviny.",
        "lecivy_prinos_text": "Tradičně míří hlavně na trávení, svíravé použití a hořký aperitivní charakter.",
        "latky_a_logika_text": "Logika je hlavně v tříslovinách, hořkých fenolických látkách a typické aromatice zelených ořechů; není to neutrální bylina.",
    },
    "Taraxacum officinale agg.": {
        "aktivni_latky_text": "hořké seskviterpenové laktony, inulin hlavně v kořeni, draslík, polyfenoly",
        "obecny_prinos_text": "Pampeliška má smysl jako hořká listová a kořenová rostlina pro trávení, jarní kuchyni i pražené nápojové experimenty.",
        "pitny_prinos_text": "Pít ji má smysl hlavně jako hořčí čaj nebo praženou kořenovou náhražku, když chceš trávící a ne sladký profil.",
        "lecivy_prinos_text": "Tradičně míří hlavně na trávení, žlučník, lehkou močovou podporu a jarní 'hořké' použití.",
        "latky_a_logika_text": "Hlavní logika je v hořčinách, draslíku a u kořene i v inulinu; právě proto je pampeliška víc funkční než delikátní.",
    },
    "Ribes nigrum": {
        "aktivni_latky_text": "vitamin C, anthokyany, flavonoidy, aromatické terpeny a ovocné kyseliny",
        "obecny_prinos_text": "Černý rybíz dává smysl hlavně jako výrazně chuťová a polyfenolová plodová i listová čajová rostlina.",
        "pitny_prinos_text": "Pít ho dává smysl kvůli výrazné vůni, kyselosti, vitaminu C a tmavým polyfenolům v plodech i zajímavé listové vůni.",
        "lecivy_prinos_text": "Tradičně míří hlavně na osvěžující a posilující pití, lehkou podporu při nachlazení a antioxidačně chápané použití.",
        "latky_a_logika_text": "Smysl dávají hlavně anthokyany, vitamin C a aromatické látky; u listu zase výrazná vůně a polyfenoly.",
    },
    "Picea abies": {
        "aktivni_latky_text": "vitamin C v mladých výhoncích, monoterpeny a další silice, pryskyřice, polyfenoly",
        "obecny_prinos_text": "Smrk je výborný hlavně pro jarní výhonkové sirupy, lesně aromatické nápoje a dýchací směsi.",
        "pitny_prinos_text": "Pít ho dává smysl kvůli výrazně lesní chuti, svěžesti mladých výhonků a tradičnímu zimně-jarnímu použití na dýchací cesty.",
        "lecivy_prinos_text": "Tradičně míří hlavně na kašel, zahlenění a respirační směsi.",
        "latky_a_logika_text": "Logika je hlavně ve vitaminu C, silicích a pryskyřici; právě to nese jak chuť, tak tradiční užití.",
    },
    "Filipendula ulmaria": {
        "aktivni_latky_text": "salicylátové deriváty, třísloviny, flavonoidy, aromatické látky",
        "obecny_prinos_text": "Tužebník je specifická aromatická květní bylina do čaje a tradičních směsí s lehce salicylátovým profilem.",
        "pitny_prinos_text": "Pít ho dává smysl hlavně kvůli mandlově medové vůni a jemně 'aspirinové' tradiční pověsti.",
        "lecivy_prinos_text": "Tradičně míří hlavně na horečnaté a nachlazovací stavy, lehčí bolest a kloubní nepohodu.",
        "latky_a_logika_text": "Smysl dávají salicylátové deriváty spolu s tříslovinami a aromatikou; přesto nejde o náhradu analgetik nebo lékařské péče.",
    },
    "Thymus vulgaris": {
        "aktivni_latky_text": "silice s thymolem a carvacrolem, flavonoidy, hořké látky",
        "obecny_prinos_text": "Tymián je výrazně funkční kuchyňská i čajová bylina s velmi jasným chuťovým a respiračním profilem.",
        "pitny_prinos_text": "Pít ho má smysl hlavně jako teplý aromatický nálev při kašli nebo na podporu trávení.",
        "lecivy_prinos_text": "Tradičně míří hlavně na kašel, zahlenění, krk a trávení.",
        "latky_a_logika_text": "Thymol a carvacrol nesou jak chuť, tak tradiční účel; tymián proto působí přímočařeji než jemné květní čaje.",
    },
    "Salix spp.": {
        "aktivni_latky_text": "salicin a další fenolické glykosidy, třísloviny, flavonoidy",
        "obecny_prinos_text": "Vrba má smysl hlavně jako historicky významná kůrová bylina s lehce salicylátovým profilem, ne jako každodenní nápoj.",
        "pitny_prinos_text": "K pití dává smysl spíš jako specifický hořkosvíravý odvar pro cílené použití než jako běžný čaj.",
        "lecivy_prinos_text": "Tradičně míří hlavně na bolest, teplotu a zánětlivě chápané stavy.",
        "latky_a_logika_text": "Logika stojí hlavně na salicinu a příbuzných glykosidech, ale přesto nejde o bezpečnou náhradu léků s kyselinou acetylsalicylovou.",
    },
    "Allium sativum": {
        "aktivni_latky_text": "organosirné sloučeniny včetně allicinu a jeho prekurzorů, flavonoidy, stopové minerály",
        "obecny_prinos_text": "Česnek je silný jako koření, macerátová a sirupová surovina i jako tradičně 'obranná' potravina.",
        "pitny_prinos_text": "Pít nebo sirupovat ho má smysl jen když jde o cílený funkční záměr, ne o chuťový komfort.",
        "lecivy_prinos_text": "Tradičně míří hlavně na nachlazení, dýchací cesty, trávení a obecně obranný režim.",
        "latky_a_logika_text": "Hlavní logika je v organosirných sloučeninách; právě ony dělají česnek ostrý, intenzivní a tradičně ceněný.",
    },
    "Achillea millefolium": {
        "aktivni_latky_text": "silice, hořčiny, flavonoidy, třísloviny, seskviterpenové laktony",
        "obecny_prinos_text": "Řebříček je hořce aromatická bylina do čajů, bitters a tradičních ženských či trávících směsí.",
        "pitny_prinos_text": "Pít ho má smysl hlavně v menším množství jako hořčí čaj nebo směs tam, kde chceš chuťově i funkčně ostřejší bylinu.",
        "lecivy_prinos_text": "Tradičně míří hlavně na trávení, spasmolytické ladění, nachlazení a ženský komfort.",
        "latky_a_logika_text": "Smysl dávají kombinace silic, hořčin a flavonoidů; právě proto je řebříček účinněji chutnající, ale ne úplně 'hebký' čaj.",
    },
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _domain_key(row: dict[str, Any]) -> str:
    return _text(row.get("domena"))


def _profile_for_scientific_name(scientific_name: str) -> dict[str, str] | None:
    return PLANT_FUNCTIONAL_PROFILES.get(scientific_name)


def build_use_functional_context(row: dict[str, Any]) -> dict[str, str]:
    scientific_name = _text(row.get("vedecky_nazev"))
    profile = _profile_for_scientific_name(scientific_name)
    domain = _domain_key(row)
    effect = _text(row.get("cilovy_efekt"))
    preparation = _text(row.get("zpusob_pripravy_nebo_vyuziti"))
    subdomain = _text(row.get("poddomena"))

    if profile:
        if domain == "pití":
            benefit = profile.get("pitny_prinos_text") or profile.get("obecny_prinos_text") or effect
        elif domain in {"fytoterapie", "léčba"}:
            benefit = profile.get("lecivy_prinos_text") or profile.get("obecny_prinos_text") or effect
        elif domain == "potrava a pití":
            benefit = profile.get("pitny_prinos_text") or profile.get("obecny_prinos_text") or effect
        else:
            benefit = profile.get("obecny_prinos_text") or effect

        return {
            "hlavni_prinos_text": benefit,
            "aktivni_latky_text": profile.get("aktivni_latky_text", ""),
            "latky_a_logika_text": profile.get("latky_a_logika_text", ""),
            "funkcni_kontext_status": "kuratorsky_profil",
        }

    fallback_benefit = effect
    if not fallback_benefit and domain == "pití":
        fallback_benefit = f"Dává smysl hlavně jako nápojové použití typu: {subdomain or preparation or 'neuvedeno'}."
    elif not fallback_benefit and domain in {"fytoterapie", "léčba"}:
        fallback_benefit = f"Smysl je hlavně v tradičním podpůrném použití typu: {subdomain or preparation or 'neuvedeno'}."
    elif not fallback_benefit:
        fallback_benefit = f"Praktický přínos vychází hlavně z použití typu: {subdomain or preparation or 'neuvedeno'}."

    return {
        "hlavni_prinos_text": fallback_benefit,
        "aktivni_latky_text": "",
        "latky_a_logika_text": "",
        "funkcni_kontext_status": "odvozeno_z_pouziti",
    }


def build_plant_functional_context(scientific_name: str) -> dict[str, str]:
    profile = _profile_for_scientific_name(_text(scientific_name))
    if not profile:
        return {
            "hlavni_prinos_text": "",
            "aktivni_latky_text": "",
            "latky_a_logika_text": "",
            "funkcni_kontext_status": "bez_kuratorskeho_profilu",
        }
    return {
        "hlavni_prinos_text": profile.get("obecny_prinos_text", ""),
        "aktivni_latky_text": profile.get("aktivni_latky_text", ""),
        "latky_a_logika_text": profile.get("latky_a_logika_text", ""),
        "funkcni_kontext_status": "kuratorsky_profil",
    }
