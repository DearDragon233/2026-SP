import re
base = r'D:\2026-SP\ManageFiles\Submission_package_Paper2'
# README
p = base + r'\README_投稿包说明.md'
s = open(p, encoding='utf-8').read()
s = s.replace("摘要/引言/方法/结果/讨论/结论/数据可用性/图注/5 表/16 条参考文献", "摘要/引言/方法/结果/讨论/结论/数据可用性/图注/5 表/15 条参考文献")
old = "| 5 | 配套诊断论文（ref 14）的引用信息 | ⚠️ 当前为 \"Manuscript in preparation\"，投稿前改为预印本或正式引用 |"
assert old in s
s = s.replace(old, "| 5 | 与诊断论文（论文 1）的关系 | ✅ 论文 1 不先发表：已从论文 2 中移除对它的引用（原 ref 14），讨论 4.4 改写为独立论证；论文 2 可单独投稿 |")
open(p, 'w', encoding='utf-8').write(s)
# Cover letter: the journal-benchmark hook cites Agronomy 2026,16,1131 (a real published paper) - keep; nothing references paper 1
c = base + r'\Cover_letter.md'
t = open(c, encoding='utf-8').read()
print("cover letter mentions companion/preparation:", bool(re.search(r"companion|in preparation|Trap of Model", t, re.I)))
