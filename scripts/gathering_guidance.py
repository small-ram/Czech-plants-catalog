from __future__ import annotations

from typing import Any


"""
Odvozené praktické doporučení ke sběru.

Záměrně generuje opatrný, stručný a ne-halašný text. Opírá se o:
- konkrétní pole v datasetu (fenologie, lokalita, rizika, legalita),
- obecné zásady sběru a hygieny z EMA GACP a AHPA Wild Collection,
- bez číselných nebo druhově specifických limitů, které nejsou v datech
  explicitně ověřené.
"""


WATER_TERMS = (
    "potok",
    "řeka",
    "prameni",
    "mokř",
    "voda",
    "tůň",
    "tuni",
    "příkop",
    "vývěr",
    "niva",
    "břeh",
)

CONTAMINATION_TERMS = (
    "kontamin",
    "silnic",
    "železn",
    "postřik",
    "psí",
    "psy",
    "kanaliz",
    "skládk",
    "dump",
    "parkovi",
    "golf",
    "ruder",
    "rumiš",
    "trávník",
    "sešlap",
    "znečiště",
)

MISIDENTIFICATION_TERMS = (
    "záměn",
    "zaměn",
    "podobn",
    "jedovat",
    "bezpečně určen",
    "bezpecne urcen",
    "miříkov",
)

PERMISSION_TERMS = (
    "vlastní",
    "vlastnich",
    "vlastních",
    "pěstovan",
    "pestovan",
    "cizí",
    "cizi",
    "souhlas",
    "legálně",
    "legalne",
    "legální",
)

PROTECTED_TERMS = (
    "chráněn",
    "chranen",
    "rezervac",
    "národní park",
    "narodni park",
    "ochran",
)

QUALITY_TERMS = (
    "plís",
    "plis",
    "hmyz",
    "nahnil",
    "poškozen",
    "poskozen",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _unique_sentences(sentences: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for sentence in sentences:
        normalized = " ".join(str(sentence or "").split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _part_specific_instruction(part_category: str, part_text: str) -> str:
    lowered_part = part_text.lower()

    if part_category == "kombinovana_cast":
        if "pupen" in lowered_part or "výhon" in lowered_part or "vyhon" in lowered_part:
            part_category = "vyhonky_a_pupeny"
        elif "květ" in lowered_part or "kvet" in lowered_part:
            part_category = "kvetni_cast"
        elif "plod" in lowered_part:
            part_category = "plodova_cast"
        elif "list" in lowered_part or "nať" in lowered_part or "nat" in lowered_part:
            part_category = "listova_nadzemni_cast"
        elif "kůr" in lowered_part or "kur" in lowered_part or "vět" in lowered_part or "vet" in lowered_part:
            part_category = "drevnata_cast"

    if part_category == "listova_nadzemni_cast":
        return "Ber hlavně mladé a zdravé listy nebo nať; neober jednu rostlinu úplně a sběr rozlož mezi více jedinců."
    if part_category == "kvetni_cast":
        return "Ber čerstvé, suché a zdravé květy nebo květenství; nech část květů na místě pro opylovače i další semenení."
    if part_category == "plodova_cast":
        return "Sbírej jen zralé, zdravé a nepoškozené plody; přezrálé, plesnivé nebo otlačené kusy hned vyřaď a část plodů nech na stanovišti."
    if part_category == "semena_a_orisky":
        return "Sbírej až plně vyzrálá a suchá semena nebo oříšky; část ponech pro obnovu porostu i pro živočichy."
    if part_category == "podzemni_cast":
        return "Podzemní části ber jen z početných populací; nevyber celé místo, po rytí zahrň zeminu zpět a pokud to dává smysl, nech část kořene nebo oddenku v zemi."
    if part_category == "drevnata_cast":
        if "kůr" in lowered_part or "kur" in lowered_part or "bork" in lowered_part:
            return "Kůru neber dokola z kmene; šetrnější je odběr z menších větví nebo z materiálu určeného k řezu."
        return "Dřevnatý materiál ber jen suchý a zdravý; nepoškozuj hlavní kmen ani nosné větve."
    if part_category == "vyhonky_a_pupeny":
        return "Ber jen malé množství mladých výhonků nebo pupenů z více rostlin; neotrhej všechny vrcholové pupeny jedné dřeviny."
    if part_category == "miza":
        return "Mízu odebírej jen z vlastních nebo výslovně povolených stromů, co nejšetrněji a jen v malém množství; strom zbytečně neoslabuj a mízu hned chlaď nebo zpracuj."
    return "Ber jen zdravý a čistý materiál, sběr rozlož mezi více rostlin a nepoškoď stanoviště víc, než je nutné."


def build_gathering_guidance(row: dict[str, Any]) -> str:
    part_category = _clean(row.get("cast_rostliny_skupina"))
    part_text = _clean(row.get("cast_rostliny"))
    period = _clean(row.get("obdobi_ziskani"))
    phenology = _clean(row.get("fenologicka_faze"))
    localities = _clean(row.get("typicke_lokality_v_CR"))
    risks = _clean(row.get("hlavni_rizika"))
    legal = _clean(row.get("legalita_poznamka_CR"))
    combined = " ".join([part_text, period, phenology, localities, risks, legal]).lower()

    sentences: list[str] = []

    if phenology and period:
        sentences.append(
            f"Sbírej jen správně určený, zdravý materiál v této fázi: {phenology}; v datech je pro něj vedené období {period}."
        )
    elif phenology:
        sentences.append(f"Sbírej jen správně určený, zdravý materiál v této fázi: {phenology}.")
    elif period:
        sentences.append(f"Sbírej jen správně určený, zdravý materiál v doporučeném období {period}.")
    else:
        sentences.append("Sbírej jen správně určený, zdravý a nepoškozený materiál.")

    sentences.append(_part_specific_instruction(part_category, part_text))

    if _contains_any(combined, MISIDENTIFICATION_TERMS):
        sentences.append("Kvůli riziku záměny sbírej jen tehdy, když máš druh jistě určený i podle určovacích znaků; při nejistotě nesklízej.")

    if _contains_any(combined, WATER_TERMS):
        sentences.append("U vodních a mokřadních stanovišť sbírej jen z čistých míst bez známek splachů, stok nebo stojaté znečištěné vody.")
    elif _contains_any(combined, CONTAMINATION_TERMS):
        sentences.append("Vyhni se lokalitám u silnic, postřiků, psích tras, skládek a jiných zdrojů kontaminace.")

    if _contains_any(legal, PERMISSION_TERMS):
        sentences.append("Preferuj vlastní, pěstované nebo výslovně povolené zdroje; na cizí pozemek ani cizí dřevinu nezasahuj bez souhlasu.")

    if _contains_any(legal, PROTECTED_TERMS):
        sentences.append("Respektuj chráněná území a druhovou ochranu; v rezervacích nebo u chráněných druhů se sběru vyhni, pokud nemáš jasné oprávnění.")

    if _contains_any(risks, QUALITY_TERMS):
        sentences.append("Každou dávku hned protřiď; plesnivý, nahnilý nebo hmyzem poškozený materiál vyřaď.")

    if part_category == "miza":
        sentences.append("Používej čisté potravinářské nádoby, mízu drž v chladu a zpracuj ji co nejrychleji, protože se rychle kazí.")
    else:
        sentences.append("Sbírej za sucha, do čisté prodyšné nádoby, bez zbytečného kontaktu se zeminou, a materiál co nejdřív zpracuj nebo usuš.")

    return " ".join(_unique_sentences(sentences))
