| Metric | v1 | v2 run1 | v2 run2 | v2-shapes run3 | v2-shapes run4 |
|---|---:|---:|---:|---:|---:|
| API calls | 12 | 19 | 18 | 13 | 20 |
| Input (prompt) tokens | 31,552 | 54,827 | 51,554 | 41,868 | 62,722 |
| Output (completion) tokens, incl. hidden reasoning | 10,683 | 10,051 | 10,400 | 12,671 | 14,312 |
| **Total tokens** | **42,235** | **64,878** | **61,954** | **54,539** | **77,034** |
| Largest single call (total) | 5132 | 5003 | 4771 | 5937 | 5108 |
| 429 retries | 0 | 0 | 0 | 0 | 0 |
| Call errors | 0 | 0 | 0 | 0 | 0 |

**Per step: input / output tokens**

| Step | v1 | v2 run1 | v2 run2 | v2-shapes run3 | v2-shapes run4 |
|---|---:|---:|---:|---:|---:|
| 1 section picking | 2,171 / 2,961 (1) | 2,171 / 2,832 (1) | 2,171 / 2,600 (1) | 2,171 / 2,297 (1) | 2,171 / 2,937 (1) |
| 2 routing | - | 15,269 / 4,466 (5) | 15,173 / 4,386 (5) | 12,514 / 3,625 (4) | 15,668 / 4,779 (5) |
| 3 extract (v1 group): cover_sampling | 5,562 / 1,096 (2) | - | - | - | - |
| 3 extract (v1 group): durability_grade | 2,544 / 758 (1) | - | - | - | - |
| 3 extract (v1 group): materials | 10,306 / 2,839 (4) | - | - | - | - |
| 3 extract (v1 group): production_curing | 10,969 / 3,029 (4) | - | - | - | - |
| 3 extract: aggregates | - | - | - | 6,965 / 3,740 (2) | 10,193 / 2,523 (3) |
| 3 extract: cover_sampling | - | 3,504 / 180 (1) | 2,830 / 162 (1) | 2,801 / 827 (1) | 5,409 / 1,510 (2) |
| 3 extract: durability | - | 9,600 / 751 (3) | 8,631 / 998 (3) | 3,800 / 673 (1) | 10,180 / 943 (3) |
| 3 extract: grade_strength | - | 2,661 / 119 (1) | 2,370 / 91 (1) | 3,184 / 113 (1) | 3,127 / 104 (1) |
| 3 extract: materials | - | 13,570 / 975 (5) | 13,346 / 1,302 (5) | 3,632 / 523 (1) | 6,822 / 701 (2) |
| 3 extract: production | - | 8,052 / 728 (3) | 7,033 / 861 (2) | 6,801 / 873 (2) | 9,152 / 815 (3) |

Cell format: input / output (number of calls). Output includes the model's hidden reasoning; Groq's usage field as logged does not split it out.
