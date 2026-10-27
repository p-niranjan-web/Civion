# Report generation guide

Map of this repository for writing the project report (for a person or an LLM). Paths are relative to
the repo root. Nothing was moved; this file only says where things are and which ones matter.

## Read first (current state)
| File | What it is |
|---|---|
| `README.md` | What Civion is and how to run it |
| `Project civion/PROJECT_OVERVIEW.md` | How the pieces fit together (written before the shapes work) |
| `Project civion/JOURNEY.md` | Owner's crisp history of stages, decisions and issues |
| `Project civion/experiments/shapes/CHANGES_SHAPES.md` | Latest big change: parameter shapes, IS 383, references, remarks; tests and BLR before/after |

## Problems and limitations
| File | What it is |
|---|---|
| `Project civion/KNOWN_ISSUES.md` | Findings on the compliance engine (not all fixed; do not implement without owner's OK) |
| `Project civion/experiments/shapes/LAYOUT_LIMITATIONS.md` | Spec layouts the fixed schema cannot handle |
| `Project civion/experiments/shapes/doc_coverage.md` | Which parameters work in which spec (BLR measured; NMP, Colombo read) |

## Pipeline experiments (localization + extraction)
| File | What it is |
|---|---|
| `Project civion/experiments/pipeline/RUNS.md` | **What v1, v2 and each run folder are** - read before any report below |
| `Project civion/experiments/pipeline/report.md` | v1 run report on BLR |
| `Project civion/experiments/pipeline/CHANGES.md` | What changed from v1 to v2 |
| `Project civion/experiments/pipeline/groups.md` | Why parameters are grouped as they are (v2) |
| `Project civion/experiments/pipeline/report_v2.md` | v2 reports; section 7 = token use (input/output per step) for v1, v2 and the shapes runs |
| `Project civion/experiments/pipeline/takeaways_v2.md` | Short v2 conclusions (recall up, cost up) |
| `Project civion/experiments/pipeline/missing_analysis.md`, `missing_analysis_v2.md` | Manual check of every MISSING parameter (v1, v2) |
| `Project civion/experiments/fallback_search/report.md`, `changes.md` | Keyword fallback search evaluation (not used in the pipeline) |

## Shapes work, details
| File | What it is |
|---|---|
| `Project civion/experiments/shapes/catalogue.md` | How requirements appear in BLR (shapes found) - BLR only |
| `Project civion/experiments/shapes/run2_vs_run4.md` | BLR before/after, field by field (`run2_vs_run3.md`: intermediate) |
| `Project civion/experiments/shapes/tokens.md` | Token table (same as report_v2 section 7) |
| `HOW_TO_ADD_PARAMETER.md` | How to add a parameter or an IS code |

## Ground truth and code (for "how it works" sections)
- IS code PDFs: `Project civion/IS Codes/` (IS 456:2000, IS 383:2016). All values in `database.py` come from these.
- `Project civion/database.py` (IS tables + parameter list), `auditor.py` (compliance check),
  `parser.py` (app extraction), `prompt_rules.py` (shared prompt rules), `test_dummy_audit.py` (tests).
- Pipeline code: `Project civion/experiments/pipeline/*.py` (`run_v2.py` is the entry point).

## Skip (generated data, not reading material)
- `experiments/pipeline/output*/**/clean.md`, `localized.md`, `*.json`, `extract_calls/` - copies of the
  document and raw LLM answers per run (evidence only).
- `experiments/parse_test/*_output.md`, `docling_samples/` - parser outputs of the sample specs.
- `Project civion/CONTEXT_HANDOFF.md` - older cold-start notes; PROJECT_OVERVIEW + JOURNEY are newer.
