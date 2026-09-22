# keyman

The typing rules of the Keyman keyboards WM Keyboard bundles, kept as a
fallback. The app downloads a keyboard's rules from keyman.com, and reads the
copy here only when keyman.com does not answer, or no longer serves that
keyboard.

812 keyboards, 25.9 MB of rules, 5.8 MB as stored. The app bundles 862 Keyman
key grids; the other 50 are published without a `.kmx`, so there are no rules
to mirror for them.

## Layout

One folder per Keyman keyboard id:

| File | What |
|---|---|
| `<id>.kmx.gz` | The compiled keyboard (`.kmx`) from the keyboard's package on downloads.keyman.com, byte for byte, gzip-compressed |
| `meta.json` | `id`, `version`, `license`, and the `sha256` and `bytes` of the uncompressed `.kmx`, plus the package URL it came from |
| `LICENSE.md` | The keyboard's own licence, naming its copyright holder |

The app checks the SHA-256 in `meta.json` and that the file parses as a
keyboard before it installs it.

## Licensing

Every keyboard here is one the Keyman API lists under the MIT licence; nothing
else is mirrored. Each folder's `LICENSE.md` is that keyboard's licence, from
its package or, where the package carries none, from beside its source in
[keymanapp/keyboards](https://github.com/keymanapp/keyboards). The `.kmx`
files are unmodified.

Keyman is a product of SIL Global. This project is not affiliated with or
endorsed by SIL Global or the Keyman project.

## Refreshing

```
python3 scripts/mirror_keyman.py
```

It reads which keyboards to mirror from a WM Keyboard checkout beside this one
(`--layouts` to point elsewhere), asks the Keyman API for each one's current
version and licence, and downloads only what changed. A keyboard that vanishes
from keyman.com keeps its folder, since that is the case the copy is for;
`--prune` drops keyboards the app stopped bundling.
