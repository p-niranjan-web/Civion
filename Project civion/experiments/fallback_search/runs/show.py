import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))['hits']
L = json.load(open('labels.json', encoding='utf-8'))
for p, hs in d.items():
    lab = L[p]; new = [h for h in hs if str(h['line']) not in lab]
    print('=====', p, len(hs), 'unlabelled:', len(new))
    for h in new:
        print(f"  L{h['line']} {h['kind']} t={h['terms']} v={h['hints']} :: {h['text'][:260]}")
