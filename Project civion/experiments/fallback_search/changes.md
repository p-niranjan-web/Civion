# Changes log: keywords_v0.json → keywords.json (and search.py)

Two refinement rounds. Every change below came from looking at BLR hits and misses, which is the point of the evaluation. The test for "general" was this: would the change help on a spec by a different author? A change counts as general if it uses only standard IS / ACI / BS wording, unit formats, or parser artefacts. None uses BLR clause numbers, BLR table numbers, or phrasing found only in BLR.

**BLR-specific changes in the final list: none.** Borderline cases are flagged inline.

Scripts that reproduce each round: `runs/make_r1.py` (v0 → `runs/keywords_r1.json`) and `runs/make_final.py` (r1 → `keywords.json`).

## Round 1

| id | where | change | reason | general / BLR-specific |
|---|---|---|---|---|
| C1 | `@kg_m3`, `@volume` | accept `m 3` (space before the 3) as well as `m3` | PDF parsers flatten superscripts, so `kg/m³` comes out as `kg/m 3`. The `kg/m3` hint failed on every cement-content value and on the chloride limit | general (parser artefact) |
| C2a | search.py | carry all leading sub-header rows of a table (unit-only rows like `Kg/m 3`, column-number rows like `(1) \| (2)` or `1 \| 2`) into each row's context, not only the first row | multi-row headers are common in spec tables, and the unit is often in the second header row | general |
| C2b | search.py | table caption = last 3 text blocks before the table (was: last 1) | a parsed table title often spans three lines: "Table N", the title, and a source line like "[IS 456 – Table 5]" | general |
| C2c | search.py | re-join a block that ends without terminal punctuation with the next block if that block starts with a lowercase word (optionally after a `- ` prefix) | Docling splits sentences at page breaks, which separated a term from its value or reference ("minimum cement content per cubic" / "- meter … Table 5 …") | general (parser artefact) |
| C3a | global exclude | the code-line regex also accepts letter list prefixes (`- h. ACI 309R …`) and the `crsi` and `aashto` prefixes | reference-list items are often lettered | general |
| C3b | global exclude | new `title_line_regex`: a unit that starts with "Specification for", "Code of practice", "Method(s) of test", "Guide for", "Standard practice for" or "Recommended practice", and has no requirement word, is a citation title | parsers split code titles from their code number ("BS 402" / "Specification for sulfate-resisting Portland cement") | general |
| C4 | cement_type terms | + sulphate/sulfate resistance and resistant, low heat, moderate heat, super(-)sulphated, rapid hardening, white cement | morphological variants of "sulphate resisting", plus the IS 269 / IS 6909 / IS 8041 cement names | general |
| C5 | compaction excludes | + "fully compacted", "compacting factor", "compacting type screeds" | "dense fully compacted concrete" is the IS 456 sulphate-table column title. Compacting factor is a workability test. "Compacting-type screeds" is ACI 301 formwork wording | general |
| C6 | curing excludes | + "days prior", "days in advance", "grout" | submittal lead times are written in days, and grout curing is a different material | general |
| C7 | transport terms | + "placed in position", "from the time", "after mixing", "of mixing", "placed", "placing", "time of production", "after batching" | time limits are usually written as "placed within N min from the time of mixing/production", not with the word "transport" | general (`placed`/`placing` were removed again in D4) |
| C8 | total_volume | new `exclude_context`: "number of samples", "sampling", "frequency", "samples" | every m³ figure in a spec's sampling-frequency table is a band boundary, not the project volume | general |
| C9 | cube size | hints: a size must sit next to cube/cylinder/mould/specimen (`15 cm cubes`, `cubes of 150 mm`, `150 x 150`), and cm is accepted. Terms + mold(s)/moulds | the old `@mm` hint fired on any mm in the sentence (slump 25 mm). Indian specs often write "15 cm cube" | general |
| C10 | sampling hints | + spelled-out counts ("one additional sample", "three cubes") | counts are often written as words | general |
| C11 | cross-reference | new `cross_ref_regex`, on for every non-descriptive parameter except total_volume. It matches "as specified/shown/given/stipulated in the Drawings / Table / IS", "conform(ing) to IS nnn", "Table N herein/below/of IS", "as per drawings/IS/table" | the task counts a cross-reference as relevant, and a deferral carries no number, so the value hint can never match it | general. Borderline: the word "herein" was added after seeing BLR's "Table 5 and Table 6 herein", but "herein" is standard contract-spec wording |
| C12 | grade excludes | + "fe", "33 grade", "43 grade", "53 grade" | steel grades (Fe 415) and cement grades (43 grade OPC) are a common false-hit pattern for "grade" | general |

Round-1 result: 76 relevant out of 135 hits (v0: 57 out of 107). Parameters with at least one relevant hit: 20 (v0: 17). New false hits: generic "cement content" hits for max cement, `placing`/`placed` for transport, aggregate "organic impurities" for water organic, and cross-references found inside table headers.

## Round 2

| id | where | change | reason | general / BLR-specific |
|---|---|---|---|---|
| D1 | search.py | the cross-reference hint applies only to prose units (sentence, list item), not to table headers or rows | "complying with IS 383" inside a table header is a label, not a deferral | general |
| D2 | search.py | terms may be raw regexes (`re:` prefix) | needed for D3 (qualifier near the term) | general (mechanism) |
| D3 | max_cement terms | removed bare "cement content", "binder content" and "quantity of cement". Only maximum-qualified forms remain: "maximum cement content", "max cement content", "maximum cementitious/binder content", a regex "cement content … shall not exceed / not more than", and a regex "maximum/upper limit … cement content" | unqualified "cement content" nearly always means the IS 456 minimum, so all 9 round-1 hits were minimum-cement rows | general |
| D4 | transport terms | removed "placed", "placing", "placed in position". Added "placed in position within", "deposited within" | bare "placed"/"placing" hit formwork-stripping tables and rebar placement | general |
| D5 | all five water_* | exclude "aggregate", "aggregates". Removed the term "organic impurities" from water_organic | aggregate deleterious-material clauses (IS 383 / IS 2386) use the same words (organic, chlorides, sulphates) | general |
| D6 | water_sulphates | exclude "sulphate resisting", "sulfate resisting" | cement-type lines mention "sulphate" | general |
| D7 | water_chlorides | exclude "admixture(s)", "calcium chloride" | admixture chloride limits are a different parameter (measured_chloride_content) | general |
| D8 | compaction excludes | + "laitance" | "remove laitance by tamping, screeding…" is standard flatwork-finishing wording | general |
| D9 | search.py | a descriptive parameter never hits a bare heading | a heading such as "Compaction of Concrete" states no requirement | general |

Final result: 76 relevant out of 109 hits (precision 0.70). 20 of 25 parameters have at least one relevant hit. Round 2 removed 26 false hits and lost no relevant hit.
