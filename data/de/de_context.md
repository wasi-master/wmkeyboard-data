# German context model — `de_context.wmlm`

Status: **candidate, G7 PASS (pre-registered exit a/b)**. This is the best measured
German model we have. The typing-strip check (c) is a post-hoc advisory, not a
gate; see [Open problems](#open-problems).

## File

| | |
|---|---|
| Path | `data/de/de_context.wmlm` |
| Size | 10,856,360 bytes |
| SHA-256 | `4fe6d6b44af85eafcda1458f6e30f991033cd96177d9f77ddf5695d294845beb` |
| Header | `German`, `langs ["de"]`, d256, 6 layers, 4 heads, ff768, ctx40, vocab 24,576 |
| Step | 88,000 |
| Heldout loss | 4.0071 (8k window) / 4.0116 (20k window) |
| Source checkpoint | `runs/G6P/90k/best.pt` |
| Source candidate | `de_candidate_g6p_90k.wmlm` |

The source candidate was exported without `--langs=de --name=German`. The
published file carries the same payload with the header corrected to
`German` / `["de"]`; the bytes after the header hash to
`c61f4e2d0b6d9d6a20c8de56272e22fb9b2b3d4e64e767aca4e9152d8f5d5144`
in both files, and `lm_probe` returns the same scores. A future re-export
from `best.pt` should produce the same file:

```bash
python tools/wmlm/export.py runs/G6P/90k/best.pt de_lm_2m/vocab.txt \
    de_context.wmlm --langs=de --name=German
```

## How it was created

This model is the G6P 90k run from the tooling in
[wasi-master/wmkeyboard#1108](https://github.com/wasi-master/wmkeyboard/pull/1108).

### Corpus

- `de_2m_mix.tsv`: 2,000,000 unique rows, 1,066,000 chat / 934,000 news
  (53.3 / 46.7).
- Sources: Tatoeba German, Leipzig News 2023, and an OpenSubtitles DE chat
  top-up (301,703 rows, 15.1 %; **licence caveat**, see below).
- `prep.py` produced `de_lm_2m`: 1,980,000 train sentences, 20,000 heldout,
  40,556,654 tokens, `vocab=24576 pieces=2048 ctx=40`,
  `seed_words=de_aosp.txt`.

### Teacher

- `Qwen3.8-27B-FP8`, vLLM, `prompt_logprobs` top-24, `max_tokens=1`.
- `de_soft_2m.npz`: 1,979,982 sentences (18 missing), 21,378,590 rows,
  top-24; 22,512 / 24,576 student words mapped (`multi=1`); 90.6 % mass;
  729 rows accepted with high NLL. The merge is a `.PARTIAL` merge, not a
  clean `.DONE`.
- Teacher A/B (100+100 fixed sentences): 27B-FP8 top-1 35.03 / 38.30
  (chat/news); 9B-Base 31.29 / 34.28; 4B-Base 29.87 / 33.07. The 27B wins
  top-1, but the 9B is slightly better on chat NLL (5.244 vs 5.278). The
  teacher choice is not fully settled.

### Student

- 90,000 steps, batch 256, d256 / 6 layers / 4 heads / ff768 / ctx40, seed 0.
- V9 word-aware alignment, `distill_alpha=0.3`, `distill_share=0.5`, no Piece
  mask, no weight, no row-0 fill.
- Best checkpoint at step 88,000, heldout 4.0071 (8k) / 4.0116 (20k).

## Evaluation

### Heldout

| Model | Heldout (8k) | Step |
|---|---:|---:|
| **G6P 90k** | **4.0071** | 88,000 |
| G6P 90k-v2 best | 4.0060 | — |
| G6P 90k-v2 best EMA | 4.0057 | — |
| 2M baseline | 4.1913 | 76,000 |
| 1.2M baseline | 4.3150 | 30,000 |

The 20k re-baseline is 4.0116 for the 90k, 4.0111 for v2, 4.0490 for 60k,
4.1207 for 30k. The 8k and 20k windows preserve the ranking.

### Glide (2,588 FUTO swipes, `blend_top1`)

| Pair | A | B | Δ | 95 % CI | p |
|---|---:|---:|---:|---|---:|
| 90k vs 2M | 0.7736 | 0.7662 | **+0.73 pp** | [+0.15, +1.31] | 0.018 |

Fixed harness: QWERTZ `KeyProximity`, no German seed pairs, the app's German
join settings and the 8 -> 16 close-stroke widening.

The 90k-v2 is not included; heldout was a wash and its Glide numbers were not
re-run with the fixed harness.

### Typing (fixed German harness, `SCATTER=careful`, n=2,000)

- Strip top-1: 0.7105 vs 2M 0.7065 = **+0.40 pp** (p = 0.096,
  CI [0.00, +0.85]).
- Per-register: chat +0.05 pp, news +0.25 pp, mean **+0.15 pp**; no slice
  degraded.
- Next-word: 0.1390 vs 0.1350 = **+0.40 pp** (p = 0.45); not significant.

## Open problems

G7 passed under the pre-registered exit; the typing strip is an advisory:

1. **Typing advisory, not a gate:** G7 passes the pre-registered exit (a) and
   (b): fixed-harness Glide +0.73 pp, CI lower +0.15 pp > 0; heldout −0.1842
   nats with Glide CI lower +0.15 pp ≥ −0.5 pp. The full-set typing strip is
   +0.40 pp; that check (c) was added after the result and is not part of the
   gate. With n=2,000 the MDE is ~2.0 pp, so the result is inconclusive; an
   8,000-case re-test is optional.
2. **Licence:** the 2M mix contains 301,703 OpenSubtitles rows (15.1 %) under
   CC BY-NC-style terms. The app code is MIT; the model is CC BY-NC, a split
   licence. The model is published with attribution and a non-commercial notice
   (operator decision, 2026-11-05). Open source is not the same as
   non-commercial; downstream commercial use of the model remains restricted.
   The maintainer can reject the data PR.
3. **Android `.so`:** not rebuilt (no Android SDK/NDK on the build host).
   The app-parity measurement is harness-only.
4. **Catalog entry:** not in this repository. It is a companion change in
   `ContextModelCatalog.kt`; the model is inert without it.
5. **Header:** the source export omitted `--langs` / `--name`; fixed in this
   copy. Re-export from `best.pt` should keep the flag.
6. **Partial soft targets:** 18 sentences missing, 729 high-NLL rows accepted;
   the tail is not marked in the file.
7. **No true tail/BOS:** top-24 is renormalized, which discards about 9.4 % of
   the teacher mass; there is no `<unk>`/OTHER bucket and no raw teacher ids.

## Teacher work deferred (cost)

A new teacher pass is **out of scope** for this PR. The existing 2M cache is
reused; a future pass needs a separately approved budget. When that happens,
fix these first:

1. **True tail + BOS:** keep raw teacher ids/probs, add a residual/OTHER
   bucket and a real BOS target. This is the largest data-side gain and
   cannot be reconstructed from the top-24 cache.
2. **One distillation contract:** `distill.py` maps single-token teacher
   words; `distill_vllm.py` uses `multi=1` word-space products. Pick one and
   use it in both.
3. **High-NLL / missing rows:** mark or retry the 729 high-NLL rows and the
   18 missing sentences; do not silently accept a `.PARTIAL` merge.
4. **Teacher choice:** re-run 27B-FP8 vs 9B-Base vs 4B-Base on a larger fixed
   set. The 27B wins top-1; the 9B is slightly better on chat NLL.
5. **Logprob width:** Together caps at 5 alternatives, and Chutes
   Qwen3.8-27B had silent MTP corruption. Use a local vLLM run with MTP off
   and 24 alternatives.
6. **G8:** finish the local 9B contract test before the next paid pass.
7. **Vocabulary:** 32k word-space targets / Piece remap; this removes the
   15.3 % Piece-row problem at the root and needs a teacher remap.

Cost reference for a future 2M pass: 5.6 h / ~€16 at 100 prompts/s, 9.34 h /
~€13.73 on an L40S, 15.9 h / ~€46 at 35 prompts/s. The current work did not
start one.

## Licensing

- Tatoeba: CC BY 2.0 FR / CC0.
- Leipzig Corpora Collection: see its terms; attribute.
- OpenSubtitles/OPUS: CC BY-NC-4.0-style; attribute opensubtitles.org and
  Lison & Tiedemann 2016. The app code is MIT; the model is CC BY-NC, a split
  licence. The model is published with attribution and a non-commercial notice
  (operator decision, 2026-11-05). Open source is not the same as
  non-commercial; downstream commercial use of the model remains restricted.
  The maintainer can reject the data PR.

## Not in this PR

Only the selected model, its `.sha256`, and this document are included.
`de_candidate_*`, the v2/EMA candidates, `de_soft_*`, `runs/`, `corpora/`,
and the other test artefacts stay out.
