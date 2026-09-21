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
