import sys
fname = sys.argv[1]
with open(fname, 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('\u201c', "'").replace('\u201d', "'")
with open(fname, 'w', encoding='utf-8') as f:
    f.write(c)
print(f"Fixed quotes in {fname}")
