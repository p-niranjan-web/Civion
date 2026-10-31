# Git history - branches and what each commit did

Two branches. `main` is the app as it is on GitHub (`origin/main`). `pipeline-localization` starts
from the last `main` commit and holds all pipeline and audit work since; it exists **only on this
laptop** (not pushed) and is **not merged** into `main`.

```
main:                   1eba41b ... 66d24d8
pipeline-localization:                 \-- 629cdc6 -- adb131a -- ... -- (latest)
```

## main (the app, 16 commits, oldest first)
| Commit | What |
|---|---|
| 1eba41b | v1.0 - first version of the app |
| 302ae42 ... fd21e20 | Vercel deployment setup: root route, api folder, requirements |
| 0f21c7d | Claude edit (general changes) |
| f663f44 | Environmental exposure selection for audits + README |
| e64a5c4, d38da24 | README updates |
| b8c9705 | Groq API key from a .env file |
| 87c01bc | .env encoding fix; PDF parsing switched to pdfplumber |
| 84aa395 | Concrete-type selector for table lookups |
| 33e3d4e | Chatbot: Markdown/LaTeX rendering; answers grounded in the audit |
| 66d24d8 | IS 383 cross-reference handling; unverified aggregate max-size check dropped |

## pipeline-localization (on top of main)
**Pipeline experiments (v1, v2)**
| Commit | What |
|---|---|
| 629cdc6 | Pipeline v1 (section picking + chunked extraction) |
| adb131a | Snapshot before the shapes work: pipeline v2, fallback keyword search, parse tests, project docs |

**Shapes / references work**
| Commit | What |
|---|---|
| 7fa8e03 | REFERENCE status (spec points to an IS code or the drawings) |
| 65d7351 | UI: REFERENCE badge, quote, pass/reference summary |
| 7c1e0fb | Table values quoted as header row + data row; verify.py checks it |
| cd97f72 | Database fixes vs IS 456: transport time (no limit), workability bands |
| 5546b7d | Shape-driven audit: PARAMETERS + one check per shape; IS 383:2016 tables |
| 79f6650 | Ledger shows extraction remarks |
| 9b1c5b9 | Pipeline: cell-by-cell table merge, multi-row table quotes, BLR run3 |
| 50a6498 | BLR run4, token split per step, doc coverage, final shapes report |
| da1b03a | Grading tables read by Python; prefer a document's own table over "as per IS 383" |
| dfd416d | Curing per IS 456 cl 13.5.1: PPC/PSC 10 days, dry hot weather 10 days |
| adea54b | Water sulphates limit is 400 mg/l as SO3 (not SO4); SO4 values converted |

**Documentation only**
| Commit | What |
|---|---|
| 3167b2b | JOURNEY.md: wide-table issue |
| cf9b4f0, 0e7a435, 13399af | RUNS.md: what v1, v2 and each run are, step by step |
| 7238cb1 | REPORT_GUIDE.md, LAYOUT_LIMITATIONS.md |
| df9a813, 764d203 | Removed DIFFICULTIES_LOG.md and STATUS.md (owner's request) |

## Practical notes
- Working branch now: `pipeline-localization`. The deployed app (`main`) has none of this work yet.
- To bring it into the app later: merge `pipeline-localization` into `main` (after review), then push.
- v4 (planned) should also be built on `pipeline-localization`, in its own experiment folder.
