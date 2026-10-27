# Git history - branches and what each commit did

Two branches. `main` is the app as it is on GitHub (`origin/main`). `pipeline-localization` starts
from the last `main` commit and holds all pipeline and audit work since; it exists **only on this
laptop** (not pushed) and is **not merged** into `main`.

```
main:                   1eba41b ... 66d24d8
pipeline-localization:                 \-- 843df8b -- 4565572 -- ... -- (latest)
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
| 843df8b | Pipeline v1 (section picking + chunked extraction) |
| 4565572 | Snapshot before the shapes work: pipeline v2, fallback keyword search, parse tests, project docs |

**Shapes / references work**
| Commit | What |
|---|---|
| 8888225 | REFERENCE status (spec points to an IS code or the drawings) |
| fc50c0a | UI: REFERENCE badge, quote, pass/reference summary |
| 0b8467c | Table values quoted as header row + data row; verify.py checks it |
| 795cbc9 | Database fixes vs IS 456: transport time (no limit), workability bands |
| a4b0111 | Shape-driven audit: PARAMETERS + one check per shape; IS 383:2016 tables |
| c45f8a7 | Ledger shows extraction remarks |
| c821823 | Pipeline: cell-by-cell table merge, multi-row table quotes, BLR run3 |
| 9e5b861 | BLR run4, token split per step, doc coverage, final shapes report |
| a2b879b | Grading tables read by Python; prefer a document's own table over "as per IS 383" |
| 245af57 | Curing per IS 456 cl 13.5.1: PPC/PSC 10 days, dry hot weather 10 days |
| 2526ab9 | Water sulphates limit is 400 mg/l as SO3 (not SO4); SO4 values converted |

**Documentation only**
| Commit | What |
|---|---|
| 48106af | JOURNEY.md: wide-table issue |
| 2a93403, 7d809c1, 3b34c7c | RUNS.md: what v1, v2 and each run are, step by step |
| 75d705b | REPORT_GUIDE.md, LAYOUT_LIMITATIONS.md |
| 5d4dadf, bcd5aa8 | Removed DIFFICULTIES_LOG.md and STATUS.md (owner's request) |

## Practical notes
- Working branch now: `pipeline-localization`. The deployed app (`main`) has none of this work yet.
- To bring it into the app later: merge `pipeline-localization` into `main` (after review), then push.
- v4 (planned) should also be built on `pipeline-localization`, in its own experiment folder.
