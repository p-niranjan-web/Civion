"""Convert every PDF/DOCX in sample_spec_docs/ to Markdown with Docling.
Run from the "Project civion" folder:  python experiments/parse_test/run_docling_samples.py
Output: experiments/parse_test/docling_samples/<name>.md  (+ run_log.txt)
"""
import pathlib, time
from docling.document_converter import DocumentConverter

src = pathlib.Path("sample_spec_docs")
out = pathlib.Path("experiments/parse_test/docling_samples")
out.mkdir(parents=True, exist_ok=True)
conv = DocumentConverter()
log = []
for p in sorted(src.iterdir()):
    if p.suffix.lower() not in (".pdf", ".docx"):
        continue
    target = out / (p.stem + ".md")
    if target.exists():
        print(f"SKIP {p.name} (already done)")
        continue
    t = time.time()
    try:
        md = conv.convert(str(p)).document.export_to_markdown()
        target.write_text(md, encoding="utf-8")
        msg = f"OK   {p.name}  {len(md)} chars  {time.time() - t:.0f}s"
    except Exception as e:
        msg = f"FAIL {p.name}  {e}"
    print(msg)
    log.append(msg)
(out / "run_log.txt").write_text("\n".join(log), encoding="utf-8")
