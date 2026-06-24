import json
from parser import parse_user_specification
import sys

def test_consistency():
    pdf_path = "downloads/50a9c069-aa54-4f98-a0ea-391798a4702c.pdf"
    print("Run 1...")
    res1 = parse_user_specification(pdf_path)
    print("Run 2...")
    res2 = parse_user_specification(pdf_path)
    
    # Strip source_quotes for comparison
    def strip_quotes(d):
        if "source_quotes" in d:
            del d["source_quotes"]
        return d
        
    r1 = strip_quotes(res1)
    r2 = strip_quotes(res2)
    
    if r1 == r2:
        print("Results match exactly!")
    else:
        print("Results differ!")
        for k in set(r1.keys()).union(set(r2.keys())):
            if r1.get(k) != r2.get(k):
                print(f"Diff at '{k}':\n  Run1: {r1.get(k)}\n  Run2: {r2.get(k)}")

if __name__ == "__main__":
    test_consistency()
