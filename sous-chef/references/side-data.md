# Datakontrakt for siden (Indkøb / Køkken / Opskrifter)

Siden er færdigbygget i `templates/side.html`. Du leverer KUN data som JSON og bygger med
`python scripts/byg_side.py data.json ud.html`. Scriptet validerer id'er, klokkeslæt,
opskrift-referencer, pris (alle varer eller ingen), `kan_reddes` og trinnenes rækkefølge, og
nægter at bygge hvis noget mangler - det er meningen, for en side der ser rigtig ud men
har dublet-id'er mister afkrydsninger i butikken uden at nogen opdager det.

## Siden vises som en artifact i chatten

Byg med `--fuld` (komplet HTML-dokument) og vis hele filen som ÉN HTML-artifact i svaret. Brugeren
åbner chatten på telefonen og har siden der - ingen links, ingen installation. Opdatér SAMME
artifact når planen ændres (nye trin, skubbet tid); lav ikke en ny hver gang. Sidens lager er nøglet
på planens `id`, så afkrydsninger og timere holder så længe `id` og vare/trin-id'erne er de samme.

**Vær ærlig om lageret.** Mens siden er åben, holder alt altid. Men siden forsøger at gemme i
browserens lager, og i flere miljøer er det blokeret - bl.a. artifacts på claude.ai, hvor
afkrydsninger typisk IKKE overlever at siden lukkes. Sig aldrig at noget overlever en lukket
side, før brugeren har set det virke; sig i stedet "hold siden åben i butikken".

Kører skillen i Claude Code (ikke i almindelig Claude), findes et Artifact-værktøj der kan
publicere filen som en privat webside med et link; brug det, hvis brugeren beder om et link.

## To omgange når det haster

1. **Første omgang, straks menuen er godkendt:** Indkøb fuld, `trin` og `opskrifter` må være
   tomme lister. Byg og vis. Det er det brugeren har brug for i butikken.
2. **Anden omgang:** skriv trin og opskrifter, byg igen, opdatér samme artifact.

Kommandoen: `python scripts/byg_side.py data.json side.html --fuld` (data.json skriver du selv i
arbejdsmappen; den behøver ikke gemmes bagefter - alt der er brug for, står i chatten og i artifacten).

**Skift ALDRIG id på en vare eller et trin der allerede er i brug** - så mister siden afkrydsningen
eller timeren for den. Nye varer får nye id'er; slettede varer forsvinder bare.

## Hvad siden gør selv (skriv det ikke i data)

- Prøver at huske afkrydsninger, "har det", aktivt trin og valgt fane i browserens lager
  (`localStorage`, nøgle `sous-chef:<id>`) - hvor lageret er tilladt. Er det blokeret (se ovenfor),
  holder tilstanden kun mens siden er åben.
- ⚠-varer sorteres øverst i deres afdeling. Antal i kurven tælles.
- "Del listen"-knappen på Indkøb sender de resterende varer som ren tekst (navigator.share,
  ellers udklipsholder) - vejen udenom browserlageret, når en anden handler.
- Køkken-fanen holder skærmen tændt (wake lock), hvor browseren tillader det.
- Køkken-fanen: swipe/knapper/piletaster mellem trin; timere gemmes som sluttidspunkt (rigtige
  efter låst skærm), flere kan køre samtidig og vises som chips øverst; lyd + vibration ved 0.
  Timere der udløb for mere end 5 minutter siden ryddes ved genåbning, så gammel snak ikke ringer.
- "Se opskrift" hopper til opskriften. Skal tidsplanen skubbes (brugeren er bagud), sker det i
  chatten: regn nye klokkeslæt og opdatér artifacten - der er ingen knap til det på siden.

## Skema

```json
{
  "id": "unik-slug-for-denne-plan",
  "titel": "Fødselsdag lørdag",
  "servering": [{"navn": "Kaffebord", "kl": "14:00"}],
  "estimat": {"samlet_min": 300, "note": "valgfri linje, fx 'heraf 3 t hvor dejen bare hviler'"},
  "indkoeb": {
    "butik_lukker": "valgfri linje øverst - kun hvis lukketid er tæt på",
    "afdelinger": [
      {"navn": "Frugt & grønt", "varer": [
        {"id": "lime", "navn": "Lime", "maengde": "10 stk", "pris": 40,
         "note": "valgfri - brug den til mængder der ser forkerte ud og til hvorfor",
         "kritisk": true}
      ]}
    ]
  },
  "trin": [
    {"id": "t1", "kl": "18:30", "titel": "kort bydeform", "ret": "hvilken ret",
     "handling": "hvad man gør, 1-3 sætninger",
     "kendetegn": "sanseindtrykket der siger det er tid - valgfri men næsten altid",
     "fejlkilde": {"tekst": "mekanismen, ikke 'pas på'", "kan_reddes": false},
     "timer_min": 40,
     "aktiv_min": 10,
     "opskrift": "id på opskrift"}
  ],
  "opskrifter": [
    {"id": "dahl", "navn": "Rød linsedahl", "antal": "10 personer",
     "ingredienser": ["..."],
     "fremgangsmaade": ["..."],
     "sekvens": [{"handling": "...", "tid": "0:20", "kendetegn": "..."}],
     "fejlkilder": [{"titel": "...", "tekst": "...", "kan_reddes": true}]}
  ]
}
```

Regler for indholdet:

- **Trin ligger i tidsplanens rækkefølge på tværs af retter** - det er tidslinjen, ikke opskriften.
  Dahlen inde i giflernes køletid er to trin efter hinanden med hver sin `ret`.
- **`kl` er planlagt starttid** i TT:MM. Ét trin pr. ting man gør, ikke pr. ret.
- **`timer_min` kun hvor man faktisk venter** (hævning, køl, simren, ovn). Ikke på "ælt dejen".
- **`aktiv_min` er hænderne i brug** på det trin - æltning 10, "vent 40 min på køl" 0. Siden
  summerer det til "X ved gryderne". `estimat.samlet_min` er første trin til servering, inkl. al
  ventetid; `estimat.note` er valgfri ("heraf 3 t hvor dejen bare hviler").
- **`pris` pr. vare i kr, tal, skøn** på dansk supermarkedsniveau for den mængde der står. Siden
  summerer til "ca. X kr at handle for" og tæller ned når man krydser af. Varer brugeren "har"
  koster 0. Sæt den på alle varer eller ingen - en halv sum lyver.
- **`sekvens`** kun for de opskrifter hvor rækkefølgen er selve opskriften (tarka, karamel,
  emulsioner) - kolonnerne er trin, handling, tid, kendetegn.
- **`kan_reddes`** sættes altid, true eller false. Det afgør hvor meget opmærksomhed fejlen fortjener.
- Vare-id'er og trin-id'er: korte, stabile slugs. Genbrug dem ved genudgivelse.

Se `templates/eksempel-data.json` for et fuldt eksempel (gifler + dahl, 5 trin, 2 opskrifter).
