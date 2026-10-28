# Mozc dictionary

`mozc-<version>.data` is Mozc's own system dictionary (`mozc.data`: the
dictionary, connection costs, segmenter, suggestion filter and the rest of
Mozc's data set), for WM Keyboard's optional Mozc engine for Japanese. The
keyboard downloads it as a CJK pack and checks it against the SHA-256 pinned
in `MozcData.kt`.

It is built, not edited: `native/mozc-jni/build.sh --data DIR` in the
keyboard's repository builds it from Mozc's sources at the release the
keyboard's `libwmmozc.so` is built from (target
`//data_manager/oss:mozc_dataset_for_oss`). The file's format belongs to that
release, so a Mozc update publishes a new file under a new name and the old
one stays for the app versions that pin it.

| File | Mozc release | Bytes | SHA-256 |
|---|---|---|---|
| `mozc-3.34.6239.data` | 3.34.6239 (`76887c679e1e4f156102e4bc62ea9cf9174678a3`) | 18,887,704 | `879a0132f03e4c5ee0ad0ca0f30b486f2e125ec82d7d9b86e0c3177d34b83ef9` |
| `mozc-3.35.6354.data` | 3.35.6354 (`0136c35782536cb43d710575c311cd4185982738`) | 19,001,738 | `7a47a2b3958baeb0796345aec2c3f380b1d783d6fa399c8a0c358a197bee6046` |

Its sources are Mozc's `src/data` (IPAdic, ICOT, the Okinawa dictionary, and
Google's additions) and the Japanese usage dictionary Mozc pins. Their
notices, with those of the library, are in `LICENSE_mozc.txt`.
