p = r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md'
s = open(p, encoding='utf-8').read()
old = "30 April of the harvest year [15]. Six features were computed"
assert old in s and s.count(old) == 1
s = s.replace(old, "30 April of the harvest year [14]. Six features were computed")
open(p, 'w', encoding='utf-8').write(s)

# full consistency check: every cited number has an entry, every entry is cited
import re
body, refs = s.split("## References")
cited = set()
for m in re.finditer(r"\[(\d+)(?:[–-](\d+))?(?:,\s*(\d+))*\]", body):
    a = int(m.group(1)); b = m.group(2)
    if b: cited.update(range(a, int(b) + 1))
    else: cited.add(a)
    for extra in re.findall(r",\s*(\d+)", m.group(0)): cited.add(int(extra))
entries = [int(x) for x in re.findall(r"^(\d+)\. ", refs, flags=re.M)]
print("reference entries:", entries)
print("cited in text   :", sorted(cited))
print("cited but missing entry:", sorted(cited - set(entries)))
print("entry never cited      :", sorted(set(entries) - cited))
