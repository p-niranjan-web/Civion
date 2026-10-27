"""Token usage per run and per step (MEASURED: Groq API usage field), as markdown.

Usage (from experiments/pipeline): python ../shapes/token_table.py
Runs: v1 (v1_results), v2 run1, run2 (before the shapes change), run3, run4 (after).
"""
import sys
from pathlib import Path

PIPE = Path(__file__).resolve().parent.parent / "pipeline"
sys.path.insert(0, str(PIPE))
from common import read_json  # noqa: E402

RUNS = [("v1", PIPE / "v1_results"), ("v2 run1", PIPE / "output_v2" / "run1"),
        ("v2 run2", PIPE / "output_v2" / "run2"), ("v2-shapes run3", PIPE / "output_v2" / "run3"),
        ("v2-shapes run4", PIPE / "output_v2" / "run4")]


def step(name):
    if name.startswith("localize"):
        return "1 section picking"
    if name.startswith("route"):
        return "2 routing"
    if name.startswith("extract[") and "] " in name:          # v1: "extract[3] materials"
        return "3 extract (v1 group): " + name.split("] ", 1)[1]
    if name.startswith("extract["):                              # v2: "extract[materials#1]"
        return "3 extract: " + name[len("extract["):].split("#")[0].split(".")[0].rstrip("]")
    return name


def tok(calls, k):
    return sum(c.get(k) or 0 for c in calls)


def main():
    data = {label: read_json(d / "run_stats.json")["calls"] for label, d in RUNS if (d / "run_stats.json").exists()}
    L = ["| Metric | " + " | ".join(data) + " |", "|---|" + "---:|" * len(data)]

    def row(label, f):
        L.append(f"| {label} | " + " | ".join(str(f(c)) for c in data.values()) + " |")
    row("API calls", len)
    row("Input (prompt) tokens", lambda c: f"{tok(c, 'prompt_tokens'):,}")
    row("Output (completion) tokens, incl. hidden reasoning", lambda c: f"{tok(c, 'completion_tokens'):,}")
    row("**Total tokens**", lambda c: f"**{tok(c, 'total_tokens'):,}**")
    row("Largest single call (total)", lambda c: max((x.get("total_tokens") or 0) for x in c))
    row("429 retries", lambda c: sum(x.get("retries", 0) for x in c))
    row("Call errors", lambda c: sum(1 for x in c if x.get("error")))
    L.append("\n**Per step: input / output tokens**\n")
    steps = sorted({step(x["name"]) for c in data.values() for x in c})
    L.append("| Step | " + " | ".join(data) + " |")
    L.append("|---|" + "---:|" * len(data))
    for s in steps:
        cells = []
        for c in data.values():
            sc = [x for x in c if step(x["name"]) == s]
            cells.append(f"{tok(sc, 'prompt_tokens'):,} / {tok(sc, 'completion_tokens'):,} ({len(sc)})" if sc else "-")
        L.append(f"| {s} | " + " | ".join(cells) + " |")
    L.append("\nCell format: input / output (number of calls). Output includes the model's hidden reasoning; "
             "Groq's usage field as logged does not split it out.")
    print("\n".join(L))


if __name__ == "__main__":
    main()
