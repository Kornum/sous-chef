# sous-chef 🍳

En Claude-skill der planlægger og gennemfører et måltid fra idé til bord - middag, fest,
fødselsdag, en enkelt ret eller en hel menu. Skillen scoper måltidet med dig, bygger en
indkøbsliste som afkrydsnings-side til telefonen og guider dig trin for trin i køkkenet
med timere og fejlkilder.

Bygget af Jakob Kornum. Skrevet på dansk, til danske køkkener.

## Hvad den gør

- **Scoper måltidet** - læser din menu kritisk (mangler den syre? for mange dejprojekter?),
  foreslår med sæsonen og siger pris og tid højt, før du beslutter dig
- **Indkøbsliste som lille app** - én HTML-side med tre faner: Indkøb (afkrydsning, prisoverslag,
  "Del listen"-knap), Køkken (ét trin pr. skærm, timere med lyd, wake lock) og Opskrifter
- **Fejlkilder med mekanisme** - ikke "pas på den brænder på", men hvorfor det går galt,
  hvordan du ser det, og om det kan reddes
- **Sanseindtryk slår klokkeslæt** - "sennepsfrøene popper - lyden er din timer"

## Struktur

```
sous-chef/
├── SKILL.md                     # selve skillen: de fem trin, tonen, reglerne
├── references/
│   ├── side-data.md             # datakontrakt for HTML-siden
│   ├── saeson.md                # dansk sæson måned for måned
│   └── vegansk.md               # de tekniske forskelle ved plantebaseret
├── scripts/
│   └── byg_side.py              # bygger siden fra JSON, validerer data (kun stdlib)
└── templates/
    ├── side.html                # den færdige side-skabelon (ingen dependencies)
    └── eksempel-data.json       # fuldt eksempel: gifler + dahl
```

## Installation

**Claude.ai / Claude-appen:** Pak mappen `sous-chef/` som zip, omdøb til `sous-chef.skill`
og upload den under Settings → Capabilities → Skills.

**Claude Code / Cowork:** Kopiér mappen `sous-chef/` til `~/.claude/skills/`.

Pak selv en `.skill`-fil med:

```bash
zip -r sous-chef.skill sous-chef
```

## Testet

Skillen er trigger-evalueret med 20 realistiske prompts (10 der skal trigge, 10 near-misses
der ikke skal) a 3 kørsler: **20/20**. Evalsættet, resultaterne og test-scriptet ligger i
[`eval/`](eval/). Validator-scriptet har desuden en negativ testsuite (dublet-id'er, halve
prissummer, manglende fejlkilde-felter afvises med klare fejl), og HTML-siden er
regressionstestet i headless Chromium.

## Design-valg

Siden er én fil uden dependencies - alt inline, ingen CDN, ingen service worker. Browserens
lager bruges hvor det er tilladt, og alt degraderer stille hvor det ikke er (fx i sandboxede
artifact-miljøer holder tilstanden kun mens siden er åben - derfor "Del listen"-knappen, der
sender listen som ren tekst udenom lageret). Valideringen bor i `byg_side.py` og nægter at
bygge en side, der ser rigtig ud men opfører sig forkert.

## Licens

MIT - se [LICENSE](LICENSE).
