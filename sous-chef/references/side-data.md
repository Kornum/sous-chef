# Datakontrakt for siden (Indkøb / Madlavning)

Siden er færdigbygget i `templates/side.html`. Du leverer KUN data som JSON og bygger med
`python scripts/byg_side.py data.json side.html --fuld`. Scriptet validerer id'er og
nedlagte felter (bl.a. klokkeslæt) og nægter at bygge hvis noget mangler - det er meningen, for en side der
ser rigtig ud men har dublet-id'er mister afkrydsninger i butikken uden at nogen opdager det.

## Publicering: én fast Artifact-side med db-lager

Brugeren har ÉN side med titlen "Sous-chef". Find den med Artifact `list` (scope `mine`) og brug
dens URL til både Artifact og ArtifactData. Lav aldrig en ny artifact, hvis den findes. Findes den
ikke, er det første gang: publicér uden `url`.

Flowet:

0. **Find siden** som beskrevet. Første gang: gem også `profil/bruger` (se nedenfor).
1. **Eksisterende plan?** ArtifactData `get` på `aktiv/plan` giver `plan_id`; `get` på
   `plandata/<plan_id>` (med `out_dir`) giver plan-JSON'en som fil - redigér den. Ny plan: nyt
   id, skriv JSON forfra i scratchpad.
2. Byg med `--fuld`.
3. Er artifacten ikke læst i denne samtale endnu: læs den først (`Artifact` med `action: "read"`
   og `url`), ellers afvises publiceringen.
4. Publicér med `url` = brugerens side (uden `url` første gang) og **altid** `capabilities: {"db": {}}` - det er en
   fuld-sæt-deklaration, så den er sikker at gentage, og uden den mister siden sit lager.
5. **Skriv planen tilbage til databasen:** `set` på `plandata/<plan_id>` (med `file_path` =
   data-JSON'en) og `set` på `aktiv/plan` = `{"plan_id": "<plan_id>"}`. Databasen er eneste
   planlager - skill-pakken er skrivebeskyttet i cloud.

**Databasens indhold** (alle mod brugerens side):

- `profil/bruger` - brugerens svar, gemt én gang: `niveau`, `hensyn`, `personer` (heltal),
  `budget_kr` (tal) og `noter` (fx hvad der er lavet før). Læses først i hver session.

- `planer/<plan-id>` - sidens egen tilstand: købt (`koebt`), fravalgt (`har`),
  ingrediens-hakker (`ingr`), aktivt trin (`trin`) og kørende timere
  (`timere`, slut-tidspunkter i epoch-ms). Siden skriver den selv; localStorage er kun lokal
  cache. Læs den når brugeren spørger "hvad mangler jeg?" i stedet for at spørge dem.
- `plandata/<plan-id>` - selve plan-JSON'en (skemaet nedenfor). Skrives af dig ved hver
  publicering.
- `aktiv/plan` - `{"plan_id": "..."}`, pointeren til den aktive plan.

To regler følger af lageret:

- **Skift ALDRIG id på en plan, vare eller et trin der er i brug** - så mister siden
  afkrydsningen eller timeren for den. Nye varer/trin får nye id'er; slettede forsvinder bare.
- Plan-id'et bruges som db-sti: kun bogstaver, tal og `. _ ~ + -`.

## To omgange når det haster

1. **Første omgang, straks menuen er godkendt:** Indkøb fuld, `trin` må være en tom liste.
   Byg og publicér. Det er det brugeren har brug for i butikken.
2. **Anden omgang:** skriv trinnene, byg igen, opdatér samme artifact.

## Hvad siden gør selv (skriv det ikke i data)

- Husker alt i artifact-db + localStorage som beskrevet ovenfor.
- Antal og pris i kurven tælles. Der er ingen advarselsikoner: det der er vigtigt ved en vare
  står i dens `note`.
- Indkøb-fanen har en knap "Kopiér listen": lægger de varer der mangler i udklipsholderen som
  kort tekst til sms: samlet prisskøn først, derefter en sektion med emoji pr. butiksafdeling
  (afdelingerne i dataene står i butiksrækkefølge, så giv dem klare navne som Frugt & grønt, Køl, Kolonial).
- Overblik-fanen: menuen med kalorier og sundhedsprikker pr. ret, kalorier pr. person, sundhedsbarometer
  (snit 1-5) og økonomibarometer (pris, pris pr. person, mod budget hvis det er sat).
- Madlavnings-fanen: trinliste øverst der kan foldes ud (alle trin med status og hop-til),
  ét trin pr. skærm med swipe/knapper/piletaster, ingrediens-hakker pr. trin,
  "Uddyb" som foldes ud, timere som chips på tværs af trin, lyd + vibration ved 0.
- Hvert trin viser varighed ("~10 min i hænderne", "20 min ventetid"), aldrig klokkeslæt.
  Der er ingen "jeg er bagud"-funktion, fordi der ingen klokkeslæt er at skubbe.

## Skema

```json
{
  "id": "unik-slug-for-denne-plan",
  "titel": "Fødselsdag lørdag",
  "personer": 10,
  "budget_kr": 900,
  "menu": [
    {"ret": "Rød linsedahl", "beskrivelse": "valgfri, én linje", "kcal_pr_person": 520,
     "sundhed": {"score": 5, "begrundelse": "bælgfrugter og grønt"}}
  ],
  "estimat": {"samlet_min": 300, "note": "valgfri linje, fx 'heraf 3 t hvor dejen bare hviler'"},
  "indkoeb": {
    "butik_lukker": "valgfri linje øverst - kun hvis lukketid er tæt på",
    "afdelinger": [
      {"navn": "Frugt & grønt", "varer": [
        {"id": "lime", "navn": "Lime", "maengde": "10 stk", "pris": 40, "maaltid": true,
         "note": "valgfri - brug den til mængder der ser forkerte ud, til hvorfor, og til om varen skal med hjem i dag"}
      ]}
    ]
  },
  "trin": [
    {"id": "t1", "titel": "kort bydeform", "ret": "hvilken ret",
     "handling": "hvad man gør, 1-3 sætninger",
     "ingredienser": ["400 g røde linser", "1 dåse hakkede tomater"],
     "kendetegn": "sanseindtrykket der siger det er tid - valgfri men næsten altid",
     "fejlkilde": {"tekst": "mekanismen, ikke 'pas på'", "kan_reddes": false},
     "uddyb": "valgfri dybde: hvorfor, hvad rigtigt ser ud som, hvad man gør hvis det går galt.\nLinjeskift er ok.",
     "timer_min": 40,
     "aktiv_min": 10}
  ]
}
```

Der er IKKE længere et `opskrifter`-afsnit og ingen `opskrift`/`sekvens` på trin - alt bor i
trinnene. Regler for indholdet:

- **Trin ligger i den rækkefølge man laver dem på tværs af retter** - det er arbejdsgangen,
  ikke opskriften. Dahlen inde i giflernes køletid er to trin efter hinanden med hver sin `ret`.
- **Hvert trin bærer alt hvad det kræver.** `ingredienser` er præcis det der bruges i DET trin,
  med vægt og mål ("400 g røde linser", ikke "linser"). Det er dig der splitter opskriften op.
  Siden viser dem som hakkeliste ("Til dette trin").
- **Mise en place-trin:** hver ret der har mere end et par ingredienser i ét ryk, starter med
  et trin hvor alt måles op ("Mål alt op til dahlen") med den fulde ingrediensliste - så er
  senere trins lister korte.
- **Sekvenser hvor rækkefølgen ER opskriften** (tarka, karamel, emulsion) skrives som flere
  små trin lige efter hinanden - ét pr. handling, hver med sit kendetegn og evt. fejlkilde.
  Det er kendetegnet ("lyden er din timer"), der bærer dem.
- **Ingen klokkeslæt.** Hverken `kl` på trin eller `servering` findes, og scriptet afviser dem.
  Ét trin pr. ting man gør. Tiden bæres af `aktiv_min`, `timer_min` og `estimat`.
- **`timer_min` kun hvor man faktisk venter** (hævning, køl, simren, ovn). Ikke på "ælt dejen".
- **`aktiv_min` er hænderne i brug** på det trin. Siden summerer til "X ved gryderne".
  `estimat.samlet_min` er første trin til færdig ret inkl. al ventetid.
- **`uddyb` er dybden** der før boede i opskriften: hvorfor, hvordan rigtigt ser ud, hvad man
  gør hvis det går galt. Foldes sammen som udgangspunkt - handling + kendetegn + fejlkilde
  skal kunne stå alene uden den.
- **`pris` pr. vare i kr, tal, skøn** på dansk supermarkedsniveau for den mængde der står.
  Sæt den på alle varer eller ingen - en halv sum lyver.
- **`kan_reddes`** sættes altid, true eller false.
- **`personer`, `menu`, `budget_kr`** bygger Overblik-fanen. `kcal_pr_person` er et skøn pr. ret
  (heltal, rundet til 10), `sundhed.score` er 1-5 med en kort `begrundelse`, begge vejledende.
  `budget_kr` er valgfri. Varer der ikke er mad får `"maaltid": false` og tæller ikke i måltidets pris.
- Vare-id'er og trin-id'er: korte, stabile slugs. Genbrug dem ved genudgivelse.

Se `templates/eksempel-data.json` for et fuldt eksempel (gifler + dahl, inkl. en sekvens
skrevet som mikro-trin).

## Plan B

Plan B gælder kun ægte fejl i en Code-session (Python nede, publicering afvist): skriv
indkøbslisten som ren tekst i chatten, sorteret efter afdeling med forklarede mængder, og
guid trinene ét ad gangen. Sig at det er nødløsningen. Lad aldrig som om siden er der, hvis den
ikke er. Mangler værktøjerne helt (almindelig chat), er svaret ikke Plan B men henvisningen i
SKILL.md: link til siden + Code-fanen.
