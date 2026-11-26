p = r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md'
s = open(p, encoding='utf-8').read()

# 1. Intro: drop the sentence that cites the unpublished companion
old_intro = (" In an earlier diagnostic on the same study system we found that apparent model skill against "
             "model-derived targets was produced by the target construction and the validation design rather "
             "than by environmental information [14].")
assert old_intro in s
s = s.replace(old_intro, "")

# 2. Section 4.4: rewrite as a self-contained argument, no reference to the companion
i = s.find("### 4.4. Relation to earlier diagnostics")
j = s.find("### 4.5. Limitations")
assert i > 0 and j > i
new_44 = ("### 4.4. Relation to target-construction effects\n\n"
          "The two findings of this study are connected. A pooled error metric rewards a model for approaching the "
          "regional yield level, and a model-derived target can supply that level through its own construction. "
          "When a yield map or a process-model output is used both to train and to evaluate a model, the level is "
          "shared by construction and the pooled score is high before any county is ranked correctly. Official "
          "statistics remove that particular sharing, and blocked validation with a training-mean baseline, as used "
          "here, shows whether anything remains. In our tests what remained was small: one arm with a positive rank "
          "correlation out of twenty. We therefore treat level-and-pattern decomposition, and not a change of target "
          "or estimator, as the step that makes a county-scale transfer test interpretable.\n\n")
s = s[:i] + new_44 + s[j:]

# 3. References: remove entry 14 and renumber 15,16 -> 14,15
old_ref14 = ("14. [Companion diagnostic paper] The Trap of Model-Derived Yield Targets: A Controlled Diagnostic of "
             "Target Construction, Validation Design, and Co-Construction Bias in County-Scale Yield Mapping. "
             "(Manuscript in preparation.)\n")
assert old_ref14 in s
s = s.replace(old_ref14, "")
assert "15. NASA Langley Research Center." in s and "16. Gao, J.; Liao, J.; Liu, Y." in s
s = s.replace("15. NASA Langley Research Center.", "14. NASA Langley Research Center.")
s = s.replace("16. Gao, J.; Liao, J.; Liu, Y.", "15. Gao, J.; Liao, J.; Liu, Y.")
# in-text citations of the moved entries
assert "[16]" in s and "[15]" in s
s = s.replace("available by 30 April [15]", "available by 30 April [14]")
s = s.replace("exists [16] but could not be obtained", "exists [15] but could not be obtained")

open(p, 'w', encoding='utf-8').write(s)
print("ref 14 removed; 4.4 rewritten; refs renumbered to 15 entries")
