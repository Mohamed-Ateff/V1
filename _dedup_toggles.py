"""Remove duplicate consecutive insight_toggle() calls (same key appears twice in a row)."""
import re

FILES = [
    r"c:\Users\moham\OneDrive\Desktop\My app\decision_tab.py",
    r"c:\Users\moham\OneDrive\Desktop\My app\signal_analysis_tab.py",
    r"c:\Users\moham\OneDrive\Desktop\My app\volume_profile_tab.py",
    r"c:\Users\moham\OneDrive\Desktop\My app\smc_tab.py",
    r"c:\Users\moham\OneDrive\Desktop\My app\regime_analysis_tab.py",
    r"c:\Users\moham\OneDrive\Desktop\My app\trade_validator_tab.py",
    r"c:\Users\moham\OneDrive\Desktop\My app\price_action_tab.py",
]

# Matches a complete insight_toggle(...) block (handles nested parens via balanced counting won't work in regex,
# so we match from `insight_toggle(` up to the closing standalone `    )\n` or `            )\n`)
# Strategy: find all positions of `insight_toggle(`, extract key string, then deduplicate consecutive same-key blocks.

def extract_toggle_blocks(txt):
    """Return list of (start, end, key) for every insight_toggle() call."""
    results = []
    for m in re.finditer(r'insight_toggle\(', txt):
        start = m.start()
        # find the key from the next quoted string
        km = re.search(r'\"([^\"]+)\"', txt[start:start+200])
        key = km.group(1) if km else '?'
        # find the closing ) — it's the line that is just whitespace + ')' after the block
        # We look for a line that is `    )\n` or `            )\n` after the opening
        pos = start + len('insight_toggle(')
        depth = 1
        while pos < len(txt) and depth > 0:
            if txt[pos] == '(':
                depth += 1
            elif txt[pos] == ')':
                depth -= 1
            pos += 1
        end = pos  # character after closing )
        # consume trailing \n if present
        if end < len(txt) and txt[end] == '\n':
            end += 1
        results.append((start, end, key))
    return results

for path in FILES:
    with open(path, 'r', encoding='utf-8-sig') as f:
        txt = f.read()
    
    original_len = len(txt)
    removed = 0
    
    # Iterate until no more duplicates found
    while True:
        blocks = extract_toggle_blocks(txt)
        changed = False
        for i in range(len(blocks) - 1):
            s1, e1, k1 = blocks[i]
            s2, e2, k2 = blocks[i + 1]
            # Check if they are consecutive (only whitespace between them) and same key
            between = txt[e1:s2]
            if k1 == k2 and between.strip() == '':
                # Remove the second block (keep the first)
                txt = txt[:s2] + txt[e2:]
                removed += 1
                changed = True
                break  # restart scan after modification
        if not changed:
            break
    
    if removed:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(txt)
        print(f"  {path.split(chr(92))[-1]}: removed {removed} duplicate(s)")
    else:
        print(f"  {path.split(chr(92))[-1]}: no duplicates found")

print("\nDone.")
