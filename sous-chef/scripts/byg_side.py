"""Fyld templates/side.html med data og skriv en færdig side.

Brug:
    python byg_side.py data.json ud.html            # fragment til Artifact-værktøjet
    python byg_side.py data.json ud.html --fuld     # komplet HTML-dokument (fallback: åbn filen direkte)

data.json skal følge skemaet i references/side-data.md.
Scriptet validerer det vigtigste (unikke id'er, klokkeslæt-format, opskrift-referencer,
pris på alle varer eller ingen, kan_reddes på alle fejlkilder, trin i tidsorden) og stopper
med en klar fejl i stedet for at levere en side der ser rigtig ud men opfører sig forkert.
"""
import json, re, sys
from pathlib import Path

HER = Path(__file__).resolve().parent
SKABELON = HER.parent / "templates" / "side.html"

# </head> og <body> er valgfrie tags i HTML; skabelonens <title>/<style> lander i head,
# og den første <div> åbner body. Så står title og style rigtigt i dokumentet.
FULD_HOVED = ('<!doctype html><html lang="da"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">')
FULD_HALE = '</html>'

KL = re.compile(r"(\d{1,2})[:.](\d{2})")


def kl_min(kl):
    m = KL.fullmatch(kl or "")
    if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def valider(d):
    fejl = []
    if not d.get("id"):
        fejl.append("mangler 'id' (bruges som nøgle for telefonens lager)")

    for s in d.get("servering", []):
        if not s.get("navn"):
            fejl.append("servering uden navn")
        if kl_min(s.get("kl")) is None:
            fejl.append(f"servering '{s.get('navn')}': kl skal være TT:MM, fik {s.get('kl')!r}")

    ids, med_pris, uden_pris = set(), [], []
    for a in d.get("indkoeb", {}).get("afdelinger", []):
        for v in a.get("varer", []):
            if not v.get("id"):
                fejl.append(f"vare uden id: {v.get('navn')}")
            elif v["id"] in ids:
                fejl.append(f"dublet vare-id: {v['id']}")
            ids.add(v.get("id"))
            if "pris" in v:
                if not isinstance(v["pris"], (int, float)):
                    fejl.append(f"vare {v.get('id')}: pris skal være et tal i kr, fik {v['pris']!r}")
                med_pris.append(v.get("id"))
            else:
                uden_pris.append(v.get("id"))
    if med_pris and uden_pris:
        fejl.append("pris skal stå på ALLE varer eller ingen - en halv sum lyver. "
                    f"Mangler på: {', '.join(str(i) for i in uden_pris[:5])}"
                    + (" ..." if len(uden_pris) > 5 else ""))

    def tjek_fejlkilde(f, hvor):
        if not isinstance(f, dict) or not isinstance(f.get("kan_reddes"), bool):
            fejl.append(f"{hvor}: fejlkilde skal have kan_reddes som true/false")

    opskrift_ids = set()
    for o in d.get("opskrifter", []):
        if not o.get("id"):
            fejl.append(f"opskrift uden id: {o.get('navn')}")
        elif o["id"] in opskrift_ids:
            fejl.append(f"dublet opskrift-id: {o['id']}")
        opskrift_ids.add(o.get("id"))
        for f in o.get("fejlkilder", []):
            tjek_fejlkilde(f, f"opskrift {o.get('id')}")

    tids, forrige, spring = set(), None, 0
    for t in d.get("trin", []):
        if not t.get("id"):
            fejl.append(f"trin uden id: {t.get('titel')}")
        elif t["id"] in tids:
            fejl.append(f"dublet trin-id: {t['id']}")
        tids.add(t.get("id"))
        kl = t.get("kl")
        if kl and kl_min(kl) is None:
            fejl.append(f"trin {t.get('id')}: kl skal være TT:MM, fik '{kl}'")
        elif kl:
            m = kl_min(kl)
            if forrige is not None and m < forrige:
                spring += 1
            forrige = m
        if "timer_min" in t and not isinstance(t["timer_min"], int):
            fejl.append(f"trin {t.get('id')}: timer_min skal være et heltal (minutter)")
        if "aktiv_min" in t and not isinstance(t["aktiv_min"], int):
            fejl.append(f"trin {t.get('id')}: aktiv_min skal være et heltal (minutter)")
        if "fejlkilde" in t:
            tjek_fejlkilde(t["fejlkilde"], f"trin {t.get('id')}")
        if t.get("opskrift") and t["opskrift"] not in opskrift_ids:
            fejl.append(f"trin {t.get('id')} peger på ukendt opskrift '{t['opskrift']}'")
    if spring > 1:
        fejl.append("trin skal ligge i tidsplanens rækkefølge (ét hop bagud er tilladt, "
                    f"når planen krydser midnat - fandt {spring})")

    est = d.get("estimat")
    if est is not None and "samlet_min" in est and not isinstance(est["samlet_min"], int):
        fejl.append("estimat.samlet_min skal være et heltal (minutter)")
    return fejl


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    fejl = valider(data)
    if fejl:
        print("Data afvist:"); [print(" -", f) for f in fejl]; sys.exit(1)
    skabelon = SKABELON.read_text(encoding="utf-8")
    # '</script' inde i data ville lukke script-tagget for tidligt
    blob = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    side = skabelon.replace("__DATA__", blob)
    if "--fuld" in sys.argv:
        side = FULD_HOVED + side + FULD_HALE
    Path(sys.argv[2]).write_text(side, encoding="utf-8")
    print(f"Skrev {sys.argv[2]} ({len(side)//1024} KB)")


if __name__ == "__main__":
    main()
