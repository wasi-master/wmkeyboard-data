# models

Small neural networks WM Keyboard downloads on demand. The app pins each file
by SHA-256 and refuses one that does not match, so a file here is never
replaced in place: a new model gets a new name.

## `cutout/u2netp.tflite`

The sticker editor's **Remove the background**, on a phone with no Google Play
services to supply ML Kit's subject segmentation.

| | |
|---|---|
| Network | U²-Net-P, the small variant of U²-Net (Qin et al., *U²-Net: Going Deeper with Nested U-Structure for Salient Object Detection*, Pattern Recognition 2020) |
| Weights | the authors' `u2netp` checkpoint, as the `u2netp.onnx` that [rembg](https://github.com/danielgatis/rembg) publishes (`sha256 309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8`) |
| Format | LiteRT / TensorFlow Lite flatbuffer, float32, converted from that ONNX with onnx2tf |
| Size | 4,575,464 bytes |
| SHA-256 | `558136589a47e97f53944ac3f65ba56f4efb5f6bae8e92b573e7c463d20fdb58` |
| Input | `input.1`, `[1, 320, 320, 3]` float32, RGB scaled by the picture's brightest value, then ImageNet mean/std |
| Output | signature `serving_default`, seven `[1, 320, 320, 1]` saliency maps; `1959` is the fused one the app reads |
| License | [Apache-2.0](https://github.com/xuebinqin/U-2-Net/blob/master/LICENSE), © Xuebin Qin et al. |

The conversion was taken from
[abhimanyu666/u2nettflite](https://huggingface.co/abhimanyu666/u2nettflite)
(Apache-2.0) and checked before it was mirrored here: run side by side with the
rembg ONNX on the same input, the largest difference on any of the seven
outputs is 3e-5.

## Meaning-based search: EmbeddingGemma 2

The keyboard's **Search by meaning**: clipboard, notes, snippets and emoji
found by what they mean, in any language, and pictures (own stickers, GIFs
saved to a pack, photos) found by what they show. One model family puts text
and pictures in the same space, so a typed query is compared with both.

These files are not in the tree. They are assets of the
[`models` release](https://github.com/wasi-master/wmkeyboard-data/releases/tag/models),
named `<sha256>-<name>` like the `natives` release beside it: pinned by the
app, never replaced, a new file gets a new digest.
`scripts/repack_embeddinggemma2.py` builds them and
`scripts/upload_embedding_models.sh` uploads them.

| | |
|---|---|
| Model | EmbeddingGemma 2 (Google, 2026): Text 270M, and the vision tower of Text Vision 440M |
| Source | `litert-community/embeddinggemma-2-text-270m-litert-lm` at `9be6e8b9`, `embeddinggemma-2-text-270m.litertlm` (`sha256 2d079ee2…0ab286fb`); `litert-community/embeddinggemma-2-text-vision-440m-litert-lm` at `e301f74d`, `embeddinggemma-2-text-vision-440m.litertlm` (`sha256 92dcbea1…4f62eb0`) |
| Change | Repackaged only: the LiteRT-LM bundle's external weight sections are written back into ordinary TFLite buffers, only the signatures the app runs are kept (shortest first, since the classic interpreter prepares subgraph 0 on load), and the int4 token table becomes a flat file the app reads without an interpreter. No weight is requantised; the kept signatures' outputs are bit-identical to the bundle's. |
| License | [Apache-2.0](https://huggingface.co/google/embeddinggemma-2), © Google |

Text (154,534,514 bytes in all):

| File | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `eg2-tokenizer.model` | 4,689,013 | `e594c8a90eb08d8bda498ff4747977dc827ae0c3c56b5c0d41a605a22d02ef03` | SentencePiece BPE model, byte fallback, 262,144 pieces (identical to `google/embeddinggemma-2`'s `tokenizer.model`) |
| `eg2-tokens.bin` | 68,157,456 | `3bc62fc4be4c2c9bc5c9902e8b41a19e698a6b218314390fa2411f4242ae5160` | `WMTE`, int32 vocabulary, int32 width (512), float32 multiplier (√512), one float32 scale per row, then rows of signed int4 pairs, low nibble first |
| `eg2-emoji-vectors.bin` | 2,648,117 | `63326576717ebaaa3d1e9da5ee040e90f7ea962876ebe3c0a655bcec468956d6` | the app's emoji catalogue (`catalog.tsv` at c848610e6, 1,716 emoji without their skin-tone variants) embedded by `scripts/embed_emoji_catalog.py` as stored texts, `<name>: <up to ten English keywords>`: `WMEV`, int32 version, int32 count, int32 width, length-prefixed UTF-8 emoji, then float16 unit vectors |
| `eg2-text-encoder.tflite` | 79,039,928 | `305850a79ab1a38a8d3862f5ac7d9500a386ac969c4f9783da6d81237ead038b` | signatures `encoder_1x{128,256,512}` (the bundle's 1024, 2048 and 8192 are left out): `embeddings` `[1, n, 512]`, `input_mask` `[1, n]` → `encodings` `[1, 768]` (L2-normalise it) |

Pictures (220,552,716 bytes more):

| File | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `eg2-vision-encoder.tflite` | 218,970,136 | `b7f069019f953e00910ad4b4b5fb029180ea3faa4fe0fa30d6fc2d37198d908b` | signature `vision_70` (the bundle's `vision_140` is left out): `images` `[1, 630, 768]` (16×16 RGB patches, 0..1), `positions_xy` `[1, 630, 2]` (-1 for padding) → `features` `[1, 70, 768]`, `mask` `[1, 70]` |
| `eg2-vision-adapter.tflite` | 1,580,532 | `fe5d26b805e24163ac495ef269490c6572255559bd17881cd0f66ce2758dfe3b` | signature `vision_adapter_70`: `soft_tokens` → `mm_embedding` `[1, 70, 512]` |
| `eg2-image-end.bin` | 2,048 | `e6599ba28ac69c35da660a0f938b589ffc94d203bcbd6797ec46df71d7c5990a` | the end-of-image embedding, 512 float32 |

A text is `<bos>`, its tokens, `<eos>`; a picture is `<bos>`, `<|image>`,
its valid soft tokens, the end-of-image embedding, `<eos>`; both go through
the text encoder. Queries take the prefix `task: search result | query: `,
stored texts `title: none | text: `. Checked through LiteRT 2.3.0 on these
exact files: English, Bengali and French texts rank as expected against each
other, and text queries pick the matching COCO photograph (cats on a sofa,
a skier, a bedroom, tennis, baseball, including a Bengali query).

## Phonetic typing: IndicXlit

The keyboard's **Neural suggestions** on the phonetic layouts for Bengali,
Hindi, Urdu, Assamese, Marathi, Gujarati, Punjabi, Odia, Tamil, Telugu,
Kannada and Malayalam: up to three readings of the word being typed, in the
suggestion strip after the one the space bar commits. One model covers all
of them, so the three files are shared.

Assets of the [`models` release](https://github.com/wasi-master/wmkeyboard-data/releases/tag/models),
named `<sha256>-<name>`. `scripts/export_indicxlit.py` builds them (the same
bytes on every run with the versions it names) and
`scripts/upload_embedding_models.sh models/indicxlit indicxlit-` uploads them.

| | |
|---|---|
| Model | IndicXlit v1.0, English to Indic (AI4Bharat, Madhani et al., *Aksharantar*, 2022): fairseq transformer, 6 + 6 layers, width 256, 11.5M parameters, 21 languages |
| Source | `indicxlit-en-indic-v1.0.zip` on the [IndicXlit v1.0 release](https://github.com/AI4Bharat/IndicXlit/releases/tag/v1.0) (`sha256 31dabc44…f169ca`), checkpoint `transformer/indicxlit.pt` (`sha256 2f03fe0d…24a09f7`) |
| Change | Exported to ONNX without fairseq (the state dict loaded into equivalent PyTorch modules), the decoder as a single step with its own self-attention cache, weights quantised to int8 (dynamic, MatMul). On the Aksharantar test words int8 is within half a point of float32. |
| License | [MIT](https://github.com/AI4Bharat/IndicXlit/blob/master/LICENSE), © AI4Bharat |

| File | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `indicxlit-encoder.int8.onnx` | 6,072,771 | `c94cd7a2e048da5d6d7f3f46e00dce13a654cb4db7afdeb03d068d730da48ce8` | `src` `[1, S]` int64 (`__<lang>__`, the letters, `</s>`) → `cross_k`, `cross_v` `[6, 1, 4, S, 64]` |
| `indicxlit-decoder.int8.onnx` | 7,070,073 | `ba94caddf41ca54202f4a439677d7a3034f8ed9f32c3ae993d87c6cda3c3140d` | `token` `[B, 1]`, `pos` `[1]`, `self_k`/`self_v` `[6, B, 4, T, 64]`, `cross_k`/`cross_v` → `logp` `[B, 806]`, `new_k`/`new_v` `[6, B, 4, T+1, 64]` |
| `indicxlit-vocab.txt` | 5,243 | `313b400545b4b08341ad10c33e2d73baaefb194c18e2d74bcdf00392efcdbea5` | `s<TAB>symbol` for the 54 source ids, then `t<TAB>symbol` for the 806 target ids, in id order |

Measured against the keyboard's own phonetic suggestions (spelling map, word
list siblings, rules) on held-out words, with the model's readings joined
after the committed one: Bengali top-4 52% → 80% on chat spellings the map
does not list, Hindi 88% → 93%; on the Aksharantar test words Bengali 30% →
80%, Hindi 55% → 84%.

## Romanized dictation: IndicXlit, Indic to English

The keyboard's **Romanized dictation model**: dictation in Hinglish, Banglish
and the other romanized languages is heard as the language itself and
written back in Latin letters, and this model spells the words of five
letters or more that the spelling maps do not know. Shorter ones stay with
the keyboard's rules. One model for every language.

Assets of the same `models` release. `scripts/export_indicxlit.py
--direction indic-en` builds them (the same bytes on every run with the
versions it names) and
`scripts/upload_embedding_models.sh models/indicxlit-latin indicxlit-latin-`
uploads them.

| | |
|---|---|
| Model | IndicXlit v1.0, Indic to English (AI4Bharat, Madhani et al., *Aksharantar*, 2022): the same fairseq transformer as above with the vocabularies swapped, 21 languages, the source tagged with its language (`encoder_langtok=src`) |
| Source | `indicxlit-indic-en-v1.0.zip` on the [IndicXlit v1.0 release](https://github.com/AI4Bharat/IndicXlit/releases/tag/v1.0) (`sha256 420d23a1…5a3322`), checkpoint `transformer/indicxlit.pt` (`sha256 45ffecef…976f28`) |
| Change | As above: exported without fairseq, the decoder as one cached step, int8 (dynamic, MatMul) |
| License | [MIT](https://github.com/AI4Bharat/IndicXlit/blob/master/LICENSE), © AI4Bharat |

| File | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `indicxlit-latin-encoder.int8.onnx` | 6,842,820 | `a6f8a8642a3fe05c4619500e5f7aada2d691ba7b91be94d5d6c0902e95bd81c2` | `src` `[1, S]` int64 (`__<lang>__`, the native characters NFC without joiners, `</s>`) → `cross_k`, `cross_v` `[6, 1, 4, S, 64]` |
| `indicxlit-latin-decoder.int8.onnx` | 6,107,507 | `2a4d5c65bb619397ed3e807d94afcdb7826ff0d42171d6ea1a694792a9cf7f57` | as above, `logp` `[B, 54]` |
| `indicxlit-latin-vocab.txt` | 5,243 | `23ff975af338afc2a6223a53f3e1261eefa4dd3438342aee00a5a76b41f2dea7` | `s<TAB>symbol` for the 806 source ids, then `t<TAB>symbol` for the 54 target ids, in id order |

Top-1 on 1,500 Aksharantar test words a language (native to Latin, a word
right when any of the test set's spellings for it came out), beam 4:

| | as | bn | gu | hi | kn | ml | mr | ne | or | pa | ta | te | ur | all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| keyboard's rules | 25.1 | 25.7 | 35.2 | 38.9 | 40.9 | 38.7 | 26.1 | 17.8 | 14.6 | 25.6 | 34.6 | 43.1 | 16.2 | 29.4 |
| model | 60.9 | 44.1 | 53.1 | 60.5 | 72.2 | 59.7 | 59.3 | 69.0 | 48.6 | 48.8 | 51.5 | 60.2 | 40.6 | 56.0 |
| model, top-4 | 81.7 | 64.9 | 74.8 | 82.5 | 88.9 | 77.9 | 75.6 | 81.9 | 69.9 | 72.4 | 72.9 | 80.1 | 64.7 | 76.0 |
| as the keyboard uses it | 57.3 | 43.6 | 52.3 | 60.1 | 71.2 | 59.3 | 57.9 | 65.3 | 46.1 | 48.5 | 51.7 | 59.5 | 35.9 | 54.5 |

"As the keyboard uses it" is the model from five native characters up and
the rules below. Short words are where the model goes wrong: on the 955
words of the keyboard's `*_rom` spelling maps that its inverted maps leave
out (mostly short, common words), the rules wrote the map's spelling for
55.1%, the model for 18.6% (की as "key", कब as "cub"), and the split for
57.5%. The model was trained on Aksharantar's training half, so the test
half favours it over the rules, which never saw it.

## Sticker generator: SDXS-512-DreamShaper and the picture filter

The keyboard's **Create stickers**: type a prompt, the phone draws the sticker.
These files are assets of the [`models` release](https://github.com/wasi-master/wmkeyboard-data/releases/tag/models),
named `<sha256>-<name>`. `scripts/build_sticker_models.sh` builds them (it runs
WM Keyboard's `tools/imagegen/convert_sd.py`), and `scripts/upload_embedding_models.sh <dir> sdxs-ds-`
and `... nsfw-` upload them. MNN writes a random model id into each file, so a
rebuild has different bytes and needs new pins in the app; the pins below are
the published files'.

| | |
|---|---|
| Model | SDXS-512-DreamShaper (Song, Sun, Yin, *SDXS: Real-Time One-Step Latent Diffusion Models with Image Conditions*, 2024): a one-step distillation of DreamShaper 8, with TAESD as its decoder |
| Source | `IDKiro/sdxs-512-dreamshaper` at `76f720262bb051da75666b22c902a78c8e16c763` |
| Change | Exported to ONNX and converted to MNN with float16 weights (run in float32). No transformer fusion: it moves the UNet's noise prediction enough that a one-step model draws another picture. Checked against diffusers on the same noise: PSNR 30.9 dB at 512 × 512 |
| License | [CreativeML Open RAIL++-M](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/blob/main/LICENSE.md) (the model's use restrictions apply to anyone who runs it); TAESD MIT |

| File | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `sdxs-ds-wmimage.json` | 489 | `6cc049f94e0b8c5f04c009df049dbdb8a017e43af6541621abe01e3835c056a0` | How to drive it: one step at t = 999, no guidance, 384 or 512 |
| `sdxs-ds-merges.txt` | 524,619 | `9fd691f7c8039210e0fced15865466c65820d09b63988b0174bfe25de299051a` | CLIP's BPE merges; the app builds the 49,408-entry vocabulary from them |
| `sdxs-ds-text_encoder.mnn` | 246,550,752 | `2c317b828bfe12f22b3a8dc51190b2e0a172ce1bcc412297399654543b3e5acb` | CLIP ViT-L/14 text encoder: `ids` [1, 77] int32 → `h` [1, 77, 768] |
| `sdxs-ds-unet.mnn` | 632,280,940 | `ebf37f1404d4114b07939863f222f191b6ff75ba5c6e042c5c3c9e7e21c25d3e` | The one-step UNet: `x` [1, 4, H/8, W/8], `t` [1], `e` [1, 77, 768] → `y` |
| `sdxs-ds-vae_decoder.mnn` | 2,465,260 | `06bb91f53739c42062559c726912d54aefde3ce14bf9fdfe6b901d37e11ed6a2` | TAESD's decoder: `z` latent → `img` [1, 3, H, W] in 0..1 |

The picture filter every generated sticker passes through:

| | |
|---|---|
| Model | NSFW image detection (Falconsai), a ViT-Base/16 at 224 × 224 |
| Source | `Falconsai/nsfw_image_detection` at `96cb0d0342c7afb80cab76ecc58b265fa44da256` |
| Change | Softmax appended, exported to ONNX, converted to MNN with 8-bit weights; probabilities match the original to four decimals on the test pictures |
| License | Apache-2.0 |

| File | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `nsfw-vit-falconsai.mnn` | 87,454,824 | `be15cad824b0161ee2f91074a4cabfaea42e034ba761b0ee50b093736e721a70` | `image` [1, 3, 224, 224] (RGB / 255, then (v − 0.5) / 0.5) → `probs` [1, 2]: normal, nsfw |

The NPU model (Stable Diffusion 1.5 as Qualcomm AI Hub compiled it for each
Snapdragon) is not here: the phone fetches it from Qualcomm's own bucket.

## Text scan: PaddleOCR PP-OCRv5 on MNN

The scanner's **Text scan** in builds without LiteRT (F-Droid's): Chinese,
Japanese and Latin-script text read on the phone. Builds with LiteRT download
the LiteRT conversion of the same models from iFleey/PPOCRv5-Android instead,
and both share the character list from there (`keys_v5.txt`, identical to the
recogniser's own list). These two files are assets of the
[`models` release](https://github.com/wasi-master/wmkeyboard-data/releases/tag/models),
named `<sha256>-<name>`. `scripts/export_ppocrv5_mnn.py <dir>` builds them and
`scripts/upload_embedding_models.sh <dir> ppocrv5-` uploads them. MNN writes a
random model id into each file, so a rebuild has different bytes and needs new
pins in the app (`PaddleOcrModel.kt`); the pins below are the published files'.

| | |
|---|---|
| Model | PP-OCRv5 mobile (PaddlePaddle, 2025): a DB text detector and an SVTR-LCNet CTC line recogniser for Simplified and Traditional Chinese, Japanese, pinyin and English |
| Source | `PaddlePaddle/PP-OCRv5_mobile_det` at `0d63e78e2b680928f6b1747d76a08db6e645efb7`, `PaddlePaddle/PP-OCRv5_mobile_rec` at `682f20538d8c086cb2128e5cfac775e6c4904e85` (the `inference.json` and `inference.pdiparams` of each, checked by SHA-256 in the script) |
| Change | paddle2onnx 2.1.0 (opset 14); an NHWC input in front and the output renamed, so the graphs take and give the same tensors as the LiteRT pair; every float constant rounded through float16 and back, as the LiteRT pair's weights are; MNN 3.6.1 converter, weights stored as float32. MNN's own float16 storage is not used: it rounds again after folding BatchNorm and misread lines the LiteRT pair reads right |
| Checked | Through the app's own pipeline on 14 rendered pages (Chinese in both scripts, Japanese including a vertical column, English, a dark page, noise and blur, rotation, a 2,000-pixel line, a 3,000 × 2,000 photo): the same text as the LiteRT pair on all 63 lines. On random inputs the largest difference from LiteRT is 3.4e-7 (detector) and 0.0093 (recogniser) |
| License | [Apache-2.0](https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE), © PaddlePaddle Authors |

| File | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `ppocrv5-det.mnn` | 4,736,960 | `284230c74bc0e395ae1f164d4ede101888f62f3507e3d5dac4125af8ac4a9a43` | `image` [1, 640, 640, 3] (BGR, ImageNet mean and deviation) → `probs` [1, 1, 640, 640], text probability per pixel |
| `ppocrv5-rec.mnn` | 16,503,532 | `9662f1605cd4e3848b7bf6f67c73315dc32349864d653784349aedb575abc330` | `image` [1, 48, 320, 3] (BGR scaled to ±1) → `probs` [1, 40, 18385], CTC classes per step: blank, the 18,383 characters, space |

## Upscale: waifu2x UpConv7 on MNN

The keyboard's **Upscale**, in the sticker editor and the gallery's photo
editor, and for small stickers sent to WhatsApp or Messenger as a 512 square:
the picture redrawn two or four times larger on the phone. These two files are
assets of the [`models` release](https://github.com/wasi-master/wmkeyboard-data/releases/tag/models),
named `<sha256>-<name>`. `scripts/export_upscalers_mnn.py <dir>` builds them and
`scripts/upload_embedding_models.sh <dir> sr-` uploads them. MNN writes a
random model id into each file, so a rebuild has different bytes and needs new
pins in the app (`UpscaleModels.kt`); the pins below are the published files'.

| | |
|---|---|
| Model | waifu2x UpConv7 (nagadomi, 2015–2017): six unpadded 3x3 convolutions with leaky ReLU and a 4x4 transposed convolution, ×2 per pass. The `noise1_scale2.0x` weights, which also undo light JPEG noise, for illustrations (`art`) and for photographs (`photo`) |
| Source | `nagadomi/waifu2x` at `cc385f97a9debfe611316aabfd5d8bb30ba2dbeb`, `models/upconv_7/{art,photo}/noise1_scale2.0x_model.json` (checked by SHA-256 in the script) |
| Change | The JSON weights loaded into the same layers in PyTorch, exported to ONNX (opset 17, height and width free) and converted with MNN 3.6.1's converter, weights stored as float32. A tile of side n + 14 comes out as exactly 2n |
| Checked | MNN against PyTorch on random tiles: largest difference 0.0015 on a 0 to 1 scale, under half of one 8-bit step. MNN's float16 compute draws wrong pixels on this network (PSNR 7 dB against float32), so the app runs float32 |
| Chosen | Measured on an Apple M2 (MNN CPU, 4 threads) against Real-ESRGAN's realesr-animevideov3, realesr-general-x4v3 and RealESRGAN_x4plus_anime_6B and waifu2x's CUNet and Swin-UNet, on OpenMoji stickers, John Tenniel's line art and Kodak photos: the most faithful (stickers ×4 with transparency 38.9 dB, Kodak ×2 31.4 dB, against 30.4 and 28.4 for realesr-animevideov3) and the fastest at photo sizes (1080p ×2 in 2.7 s, against 11.8 s and 23.6 s for the compact Real-ESRGAN networks; ONNX Runtime 12.7 s on the same network) |
| License | [MIT](https://github.com/nagadomi/waifu2x/blob/master/LICENSE), © 2015 nagadomi |

| File | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `sr-waifu2x-upconv7-art.mnn` | 2,212,756 | `a01167275376f18e224a17cf24e2f1dcec5bb636d21d7bf460abd5451631dd84` | `image` [1, 3, H, W] RGB from 0 to 1 → `upscaled` [1, 3, 2(H − 14), 2(W − 14)]: stickers, drawings, screenshots |
| `sr-waifu2x-upconv7-photo.mnn` | 2,212,756 | `7a306a9e37f86d3a48ec9d17724771b4229ebaf64f694c8534ca7e162be5704d` | The same, trained on photographs |

## Dictation punctuation: punctuation-restoration-small

The keyboard's **Add punctuation and capitals**: full stops, commas and
question marks put back into the bare words two of its offline voice engines
write (Sherpa, Omnilingual), in 88 languages. These three files are assets of
the [`models` release](https://github.com/wasi-master/wmkeyboard-data/releases/tag/models),
named `<sha256>-<name>`. `scripts/export_punctuation.py <dir>` builds them and
`scripts/upload_embedding_models.sh <dir> punct-` uploads them. The build is
deterministic: two runs wrote the same weights byte for byte.

| | |
|---|---|
| Model | punctuation-restoration-small v1.1 (Horizon Labs, 2026): mmBERT-small token classification, one label per word on its last token: nothing, `.` `,` `?` `-` `:` |
| Source | `Horizon-Labs/punctuation-restoration-small` at `ee31fdfc5304f876ea3b0dd72d30eda7e940b2b1`: `onnx/model.onnx` (fp32), `tokenizer.json`, `config.json`, each checked by size and SHA-256 in the script |
| Change | The token table quantised to int8 with a scale per row and dequantised after its Gather; every MatMul quantised weight-only to 8 bits (MatMulNBits, blocks of 32, symmetric, int8 compute); the weights written to an external data file, which ONNX Runtime maps instead of copying. The tokenizer's 256,000 pieces written as a SentencePiece BPE `ModelProto`, each piece scored by the rank of the first merge that makes it |
| Checked | Labels identical to the fp32 model on the script's samples; on FLORES-200 (200 paragraphs each of en, bn, hi, es, ar, zh, ru, fr) the same F1 as fp32 in every language. The tokenizer, run the app's way (BPE by piece score, a word at a time), gives Hugging Face tokenizers' ids on 3,200 test texts. Built with onnxruntime 1.31.0 and checked on 1.30.0, the app's |
| Chosen | Measured against 1-800-BAD-CODE's punct_cap_seg_47_language and xlm-roberta_punctuation_fullstop_truecase and sherpa-onnx's CT-Transformer: the best punctuation in all eight languages on FLORES. See `native/sherpa-onnx-jni/README.md` in the app repository |
| License | [Apache-2.0](https://huggingface.co/Horizon-Labs/punctuation-restoration-small), © Horizon Labs; built on [mmBERT](https://huggingface.co/jhu-clsp/mmBERT-small) (MIT, Johns Hopkins University) |

| File | Bytes | SHA-256 | What it is |
|---|---:|---|---|
| `punct-mmbert-small.onnx` | 588,015 | `1d0ac3af30fa5de2c913f3ab80b26a94a790a988a270adcb239a3a5248f0efe7` | The graph: `input_ids`, `attention_mask` [1, n] int64 → `logits` [1, n, 6]; `<bos>` (2) first and `<eos>` (1) last |
| `punct-mmbert-small.onnx.data` | 145,913,856 | `1927826af2b8dae8b879aec82647c74fd26ca79645fb300934607e60f0f526ae` | Its weights, the external data the graph names: keep the file name |
| `punct-mmbert-small.model` | 4,747,941 | `13cb25eeae71780a9e52d3771ebbc59a7a0eb2274ebcb20e203d68460f93a6d4` | SentencePiece BPE model, byte fallback, 256,000 pieces |

## Smart punctuation key: `punct/smart_punct_v2.wmpt`, `punct/smart_punct_v2_large.wmpt`

The keyboard's **Smart punctuation key** for 58 languages at once: the key
beside the spacebar shows the mark the sentence so far is heading for.
Trained by the app repository's `tools/wmpunct` (see its README) on a rented
RTX 5080; `wm-engine/src/punct.rs` reads it. `v2` is the Standard size the
switch fetches by itself, `v2_large` the Large one offered under it.

| | Standard `v2` | Large `v2_large` |
|---|---|---|
| Network | encoder, embedding 64 → 192, 4 layers, 4 heads, feed-forward 512 | embedding 96 → 256, 6 layers, 4 heads, feed-forward 768 |
| Parameters | 4.6M | 8.8M |
| Training | 60,000 steps of 512, 0.73 epochs | 100,000 steps of 512, 1.2 epochs |
| Held-out accuracy over `. ? !`, all languages | 87.2% | 87.5% |
| English | 93.7% (`?` precision .94, recall .86) | 93.9% (`?` .94 / .87) |
| Size | 5,255,776 bytes | 9,476,584 bytes |
| SHA-256 | `5e463c42eea1d308273d89e39275d033a5fbf8e3b83a2e6987407679e9489ad2` | `24b755df006a7ae4066182685b9287bb30c91aaac9c636972e9a955bce2cb381` |

Shared by both: vocabulary of 49,152 tokens (4 specials, 40,956 words shared
out between the languages by the square root of their token counts, 8,192
subword pieces); context 48 tokens; 4 classes `.` `?` `!` `,`; `WMPT`
version 1 container (the `.wmlm` layout, int8 weights with a scale per row,
f32 norms, biases and head).

Data: Tatoeba per-language exports and OPUS OpenSubtitles 2018 (streamed,
line-capped per language), 41.4M examples after the filter and dedupe,
40,000 held out. Languages (keyboard ids): af ar az bg bn bs ca cs da de el
en eo es et eu fa fi fr gl he hi hr hu hy id is it ka kk lt lv mk ml mr ms nb
nl pl pt pt_br ro ru si sk sl sq sr sv sw ta te tl tr uk ur uz vi. Russian is
Tatoeba only; Latvian subtitles only. Accuracy by language runs from .95
(Esperanto, Turkish) and .94 (English) to .72 (Persian) and .76 (Bengali,
whose data is short subtitle lines); the exclamation mark is almost never
predicted (recall .02), questions asked in statement order are the other
miss.

License: the models are MIT like the keyboard; Tatoeba text is CC BY 2.0 FR,
OpenSubtitles text is the OPUS corpus.

## Smart punctuation key: `punct/smart_punct_v1.wmpt`

The keyboard's **Smart punctuation key**: the key beside the spacebar shows
the mark the sentence so far is heading for. Trained by the app repository's
`tools/wmpunct` (see its README); `wm-engine/src/punct.rs` reads it.

| | |
|---|---|
| Network | bidirectional transformer encoder, factorised embedding 64 → 160, 3 layers, 4 heads, feed-forward 448, context 48 tokens, 4 classes (`.` `?` `!` `,`); 1.8M parameters |
| Vocabulary | 16,384 tokens: 4 specials, 12,284 words shared between the languages, 4,096 subword pieces (the context model's `▁`/`##` scheme) |
| Data | Tatoeba English and German sentences and the first 400,000 lines of OPUS OpenSubtitles 2018 English; 2.9M examples after the filter, 5,000 held out |
| Accuracy | 97.3% of held-out sentence ends right over `. ? !` (English 98.0%, German 95.0%); `?` precision .96 recall .94; `!` recall .23 |
| Format | `WMPT` version 1: the `.wmlm` container, int8 weights with a scale per row, f32 norms, biases and head |
| Size | 2,077,464 bytes |
| SHA-256 | `2cdac4e7ff15b902a3cedc6ebd8f61ec579af8de0c9b8b04728fa5b8c288163d` |
| License | the model is MIT like the keyboard; Tatoeba text is CC BY 2.0 FR, OpenSubtitles text is the OPUS corpus |

Replaced by `v2` above; kept because a new model is a new file name, never a
replaced file.
