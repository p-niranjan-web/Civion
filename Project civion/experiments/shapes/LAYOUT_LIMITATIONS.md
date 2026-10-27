# What the fixed structure cannot handle (layout differences between specs)

Our schema has fixed fields and fixed forms (value, range, table, reference). These are the cases,
seen in BLR, NMP Noida and Colombo, that do not fit. **Seen in** = where it was found (BLR measured;
NMP / COL from reading). None is built; each would need its own new structure.

| # | Case | Seen in | What happens now |
|---|---|---|---|
| 1 | Grade given per structural member (pile M30, deck M40...) | COL | One `specified_grade` field; the model must pick one or return null |
| 2 | Cover given per structural element (pile, pier, deck) | COL | `member_covers` only has Beams / Columns / Slabs |
| 3 | Minimum cement given per grade, not per exposure | NMP | Our check looks it up by exposure (IS 456 Table 5), so the value cannot be compared |
| 4 | Chloride limit as % of cement, not kg/m3 of concrete | NMP, COL | Unit differs; not converted, not audited |
| 5 | Water limits as total dissolved solids, not organic / inorganic | NMP | No matching field; dropped |
| 6 | Value that depends on a condition (cube 100 or 150 mm by aggregate size; mass-concrete or hot-weather values) | COL, BLR | A field holds one value; the condition is lost (a remark may mention it) |
| 7 | Two different values for one field (w/c 0.55 table vs 0.5-0.52 clause) | BLR | First in document order is audited; a remark shows both |
| 8 | Same table twice, one copy garbled by the parser (sampling table) | BLR | First copy may be used; bands can be wrong |
| 9 | Sampling rule per batch / per day (BS style), not per volume band | COL | Does not fit the `sampling` shape |
| 10 | Requirement deferred to a non-IS code (BS 882, BS EN 1008, ASTM) | COL | Counted as REFERENCE (pass), same as an IS reference |
| 11 | Requirements matching none of our 37 parameters (placing temperature, free fall, fineness modulus...) | all | Dropped silently ("extras" list not built) |
| 12 | Table designation names that are not IS 383 names (e.g. a non-standard nominal size) | - (not seen yet) | Reported as "not in IS table"; that part is not audited |
| 13 | Acceptance / trial-mix criteria written as rules (average of 3 cubes, freak results...) | BLR, NMP, COL | No shape for multi-condition rules; not audited |
| 14 | Old IS 456 tables in a spec (3 exposure classes instead of 5) | BLR | Works only because the user picks the exposure; a class missing from the spec's table gives no value |

Also not layout but model behaviour (same input, different answer between runs): curing 7 vs 14 days,
grading table read vs "as per IS 383" (BLR run2/run3/run4).
