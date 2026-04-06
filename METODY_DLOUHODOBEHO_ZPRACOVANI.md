# Metody Dlouhodobého Zpracování

## Co se nově modeluje

Projekt nově nepracuje jen s jednou textovou `forma_uchovani`, ale i s explicitní vrstvou více metod dlouhodobého potravinového zpracování.

To je důležité proto, že jedno použití může reálně zahrnovat několik paralelních možností, například:

- sušení
- sirup
- zavaření
- džem
- kompot

## Aktuální slovník metod

Aktuálně je v `vocab_processing_methods` těchto `14` metod:

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

## Aktuální pokrytí

Stav po posledním rebuild:

- `273` celkových použití
- `148` použití s alespoň jednou metodou
- `72` rostlin s alespoň jedním takovým použitím
- `240` vazeb `use_processing_methods`

Počty podle metod:

- `Sušení`: `76`
- `Sirup / koncentrát`: `42`
- `Zavaření / sterilace ve sklenici`: `34`
- `Cukrování / kandování / džem`: `27`
- `Kvašení / fermentace`: `20`
- `Naložení do octa / ocet`: `8`
- `Tinktura / alkoholová macerace`: `8`
- `Kompot`: `8`
- `Nakládání`: `7`
- `Skladování v chladu`: `6`
- `Mražení`: `4`
- `Pasterace`: `0`
- `Sterilizace`: `0`
- `Naložení do oleje / olej`: `0`

## Příklady vícemetodových použití

Silné příklady, kde jedna položka přirozeně kombinuje více cest:

- `R049` `borůvka černá`: `Sušení · Sirup / koncentrát · Zavaření / sterilace ve sklenici · Cukrování / kandování / džem · Kompot`
- `R008` `bez černý`: `Sirup / koncentrát · Zavaření / sterilace ve sklenici · Tinktura / alkoholová macerace · Cukrování / kandování / džem`
- `R073` `višeň obecná`: `Sirup / koncentrát · Zavaření / sterilace ve sklenici · Cukrování / kandování / džem · Kompot`
- `R074` `rybíz černý`: `Mražení · Sirup / koncentrát · Zavaření / sterilace ve sklenici · Cukrování / kandování / džem`

## Auditní poznámky

Současný model je užitečný, ale zatím ještě není plně explicitní v samotném workbooku.

Metody se dnes odvozují z:

- `poddomena`
- `zpusob_pripravy_nebo_vyuziti`
- `forma_uchovani`

To znamená:

- výsledek je velmi praktický pro appku a filtraci
- ale pořád jde částečně o heuristické odvození z volného textu

V dubnu 2026 byla heuristika zpřesněna tak, aby se nechytila falešně na substring uvnitř jiného slova.

Konkrétní opravený typ chyby:

- `želé` už se nevyhodnotí jen proto, že text obsahuje `zelenina`

## Co by bylo ideální dál ve workbooku

Nejlepší další redakční krok je přidat do workbooku explicitní vícenásobné pole, například:

- `metody_dlouhodobeho_zpracovani`

Doporučený formát:

- hodnoty oddělené `;`
- jen ze schváleného slovníku
- možnost zapsat více metod současně

Praktický příklad:

```text
sušení; sirup; zavaření; džem; kompot
```

## Doporučené další kroky

1. Přidat explicitní pole metod přímo do workbooku a přestat se spoléhat hlavně na heuristiky.
2. Dopsat editorům krátká pravidla, kdy je položka `zavaření`, kdy `sterilizace`, kdy `pasterace` a kdy současně `džem`.
3. Rozšířit dataset hlavně o podreprezentované metody: `mražení`, `olej`, `pasterace`, `sterilizace`, `chlazené skladování`.
4. U víceúčelových plodů systematicky doplnit všechny běžné dlouhodobé cesty, ne jen jednu reprezentativní.
