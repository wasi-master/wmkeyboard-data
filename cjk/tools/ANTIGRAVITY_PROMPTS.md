
---

# Follow-up: jyutping.tsv cleanup

Validation of the generated tables found `cangjie.tsv`, `s2t.txt` and
`jyutping_syllables.txt` clean. `jyutping.tsv` has one real issue: **282 rows whose
"word" is Latin text, not Han**. The keyboard drops them, but they also waste index
space and are meaningless in a Chinese IME.

(A further 1289 rows that failed the segmentation cross-check were a bug in the
keyboard's segmenter, now fixed — no action needed on the data for those.)

```
Clean up ~/Work/wmkeyboard-data/cjk/jyutping.tsv, and update
~/Work/wmkeyboard-data/cjk/tools/build_jyutping_dict.py so a rebuild stays clean.

PROBLEM 1 — Latin-text entries (282 rows). CC-Canto contains entries whose headword is
English or mixed, which do not belong in a Chinese input dictionary. Examples of the
reading/word pairs currently present:
    aahet    亞head
    aaipi    IP
    angkou   uncle
    aulet    outlet
    beibifet baby-fat
DROP any row whose word field contains a Latin letter (A-Z or a-z). A word must be
entirely Han characters and CJK punctuation.

PROBLEM 2 — 8 rows with non-standard romanizations that do not match the syllable
inventory in jyutping_syllables.txt:
    dut 嘟, heiyo 嗨喲, jinye 演野, sengyat 成日, seu 蛇, wou 㕵, yukyuk 郁郁,
    yutkungjyugingwai 愈窮愈見鬼
Check each against standard LSHK Jyutping. Most look like source typos or variant
spellings (蛇 is se4, not seu; 演野 is jin2 je5, so jinje not jinye). Correct the
reading where the standard form is clear, and drop the row where it is not.

THEN re-run the segmentation cross-check that the build script already performs — every
reading must split into syllables from jyutping_syllables.txt using longest-match with
backtracking — and confirm zero failures.

REPORT: rows before, rows dropped by reason, rows after, and the new
  shasum -a 256 jyutping.tsv   and   wc -c jyutping.tsv
so the app's CjkDictCatalog entry can be updated.
```

**After regenerating, the checksum in the app must be updated** — `CjkDictCatalog.kt`
currently pins `sha256 = 955764a4bbff61b62de9fb55d4f1fd78c25e995b00ee2afdfdc0a005ae06ea3c`
and `sizeBytes = 2_993_536L`. A mismatch makes the download fail verification, which is
the intended behaviour but will look like a network bug.
