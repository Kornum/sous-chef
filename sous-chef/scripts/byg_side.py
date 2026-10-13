"""Fyld templates/side.html med data og skriv en færdig side.

Brug:
    python byg_side.py data.json ud.html            # fragment
    python byg_side.py data.json ud.html --fuld     # komplet HTML-dokument (brug denne til publicering)

data.json skal følge skemaet i references/side-data.md (to faner: Indkøb og Madlavning).
Scriptet validerer det vigtigste (unikke id'er, nedlagte felter som klokkeslæt) og stopper
med en klar fejl i stedet for at levere en side der ser rigtig ud men opfører sig forkert.
"""
import json, re, sys
from pathlib import Path

HER = Path(__file__).resolve().parent
SKABELON = HER.parent / "templates" / "side.html"

FULD_HOVED = ('<!doctype html><html lang="da"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'
              '</head><body>')
FULD_HALE = '</body></html>'


def valider(d):
    fejl = []
    if not d.get("id"):
        fejl.append("mangler 'id' (nøgle for lager i localStorage og artifact-db)")
    elif not re.fullmatch(r"[A-Za-z0-9._~+-]+", d["id"]):
        fejl.append(f"id '{d['id']}' er ugyldigt som db-sti: brug kun bogstaver, tal og . _ ~ + -")
    if d.get("servering"):
        fejl.append("'servering' er nedlagt: planen har ingen klokkeslæt eller leveringstidspunkt. "
                    "Fjern feltet, og skriv varigheden i estimat")
    if "opskrifter" in d:
        fejl.append("'opskrifter' findes ikke længere - al detalje bor i trinnene (se references/side-data.md)")
    ids = set()
    for a in d.get("indkoeb", {}).get("afdelinger", []):
        for v in a.get("varer", []):
            if not v.get("id"):
                fejl.append(f"vare uden id: {v.get('navn')}")
            elif v["id"] in ids:
                fejl.append(f"dublet vare-id: {v['id']}")
            ids.add(v.get("id"))
            if "pris" in v and not isinstance(v["pris"], (int, float)):
                fejl.append(f"vare {v.get('id')}: pris skal være et tal i kr, fik {v['pris']!r}")
    tids = set()
    for t in d.get("trin", []):
        if not t.get("id"):
            fejl.append(f"trin uden id: {t.get('titel')}")
        elif t["id"] in tids:
            fejl.append(f"dublet trin-id: {t['id']}")
        tids.add(t.get("id"))
        if not t.get("titel"):
            fejl.append(f"trin {t.get('id')}: mangler titel")
        for gammel in ("opskrift", "sekvens"):
            if gammel in t:
                fejl.append(f"trin {t.get('id')}: '{gammel}' findes ikke længere - skriv detaljen ind i trinnet "
                            "(ingredienser/handling/uddyb), en sekvens bliver til flere små trin")
        if "kl" in t:
            fejl.append(f"trin {t.get('id')}: 'kl' er nedlagt - ingen klokkeslæt på trin. "
                        "Skriv varigheden i aktiv_min og timer_min i stedet")
        if "timer_min" in t and not isinstance(t["timer_min"], int):
            fejl.append(f"trin {t.get('id')}: timer_min skal være et heltal (minutter)")
        if "aktiv_min" in t and not isinstance(t["aktiv_min"], int):
            fejl.append(f"trin {t.get('id')}: aktiv_min skal være et heltal (minutter)")
        ing = t.get("ingredienser")
        if ing is not None and (not isinstance(ing, list) or not all(isinstance(x, str) for x in ing)):
            fejl.append(f"trin {t.get('id')}: ingredienser skal være en liste af tekster ('400 g røde linser')")
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
