"""Trigger-eval mod den RIGTIGE installerede skill: kalder claude -p og tjekker
om Skill-værktøjet invokeres med skill == "sous-chef"."""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

EVAL = json.load(open('/home/claude/sous-chef-fix/eval/trigger-eval.json'))
RUNS = 3
env = {k: v for k, v in os.environ.items() if k != 'CLAUDECODE'}

def one(query):
    try:
        r = subprocess.run(['claude','-p',query,'--output-format','stream-json','--verbose','--model','claude-fable-5'],
                           capture_output=True, text=True, timeout=90, env=env, cwd='/root')
    except subprocess.TimeoutExpired:
        return None
    for line in r.stdout.splitlines():
        try: e = json.loads(line)
        except: continue
        if e.get('type')=='assistant':
            for c in e.get('message',{}).get('content',[]):
                if c.get('type')=='tool_use' and c.get('name')=='Skill' and c.get('input',{}).get('skill')=='sous-chef':
                    return True
    return False

jobs = [(i, item, r) for i, item in enumerate(EVAL) for r in range(RUNS)]
res = {}
with ThreadPoolExecutor(max_workers=10) as ex:
    futs = {ex.submit(one, item['query']): (i, item) for i, item, _ in jobs}
    for f in futs:
        pass
    for f, (i, item) in list(futs.items()):
        res.setdefault(i, []).append(f.result())

ud = []
for i, item in enumerate(EVAL):
    runs = [x for x in res[i] if x is not None]
    rate = sum(runs)/len(runs) if runs else -1
    ok = (rate >= 0.5) == item['should_trigger'] and runs
    ud.append({'query': item['query'], 'should_trigger': item['should_trigger'],
               'rate': f"{sum(runs)}/{len(runs)}", 'pass': bool(ok)})
    print(('PASS' if ok else 'FAIL'), f"{sum(runs)}/{len(runs)}", 'exp=' + str(item['should_trigger']), item['query'][:70])
print('TOTAL:', sum(1 for u in ud if u['pass']), '/', len(ud))
json.dump(ud, open('/home/claude/sous-chef-fix/eval/resultat.json','w'), ensure_ascii=False, indent=1)
