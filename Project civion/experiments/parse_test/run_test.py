"""Parsing comparison: docling vs pymupdf4llm. Saves raw Markdown as-is.

Usage: python run_test.py [pdf_path]
Outputs are written next to this script.
"""
import sys
import time
import traceback
import warnings
import logging
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "BLR Airport (Cast-in-Concrete).pdf"

logging.basicConfig(level=logging.WARNING)
results = {}


def run(name, fn, out_name):
    print(f"\n=== {name} ===", flush=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        t0 = time.perf_counter()
        try:
            md = fn()
            elapsed = time.perf_counter() - t0
            (HERE / out_name).write_text(md, encoding="utf-8")
            results[name] = (elapsed, len(md), None)
        except Exception:
            elapsed = time.perf_counter() - t0
            results[name] = (elapsed, 0, traceback.format_exc())
    for w in caught:
        print(f"WARNING [{name}]: {w.category.__name__}: {w.message}")
    elapsed, n, err = results[name]
    print(f"{name}: {elapsed:.2f}s, {n} chars" + (f"\nERROR:\n{err}" if err else ""))


def docling_run():
    from docling.document_converter import DocumentConverter
    conv = DocumentConverter()
    return conv.convert(str(PDF)).document.export_to_markdown()


def pymupdf_run():
    import pymupdf4llm
    return pymupdf4llm.to_markdown(str(PDF))


print(f"PDF: {PDF}")
run("docling", docling_run, "docling_output.md")
run("pymupdf4llm", pymupdf_run, "pymupdf4llm_output.md")

print("\n=== SUMMARY ===")
for k, (t, n, e) in results.items():
    print(f"{k}: {t:.2f}s | {n} chars | {'ERROR' if e else 'ok'}")
