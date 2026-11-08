#!/usr/bin/env bash
# Rebuilds the Khipro glide tables, the Khipro spellings of every word of
# data/bn/bn_full.txt.gz (wasi-master/wmkeyboard#593):
#
#   data/bn/bn_khipro_glide.txt.gz       Khipro Classic
#   data/bn/bn_khipro_dark_glide.txt.gz  Khipro Dark, which spells most words
#                                        differently (হবে: Classic hobe, Dark hbe)
#
# Runs WM Keyboard's own romanizer (native/wm-engine, the Rust engine the app
# calls), so the tables are exactly what the app would work out on a phone.
# Rerun whenever bn_full.txt.gz changes, when the bundled Khipro specs change,
# or when the app bumps KhiproGlideSpellings.VERSION. About ten minutes each on
# a laptop.
#
#   scripts/build_bn_khipro_glide.sh [path/to/WMKeyboard]
#
# Needs cargo.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$(cd "${1:-$ROOT/../WMKeyboard}" && pwd)"
ENGINE="$APP/native/wm-engine"

cargo build --release --manifest-path "$ENGINE/Cargo.toml" --example khipro_glide_table
BIN="$ENGINE/target/release/examples/khipro_glide_table"

build() { # <output name> [--dark]
    local out="$ROOT/data/bn/$1"
    shift
    gzip -dc "$ROOT/data/bn/bn_full.txt.gz" | "$BIN" "$@" | gzip -9n > "$out.part"
    mv "$out.part" "$out"
}

build bn_khipro_glide.txt.gz
build bn_khipro_dark_glide.txt.gz --dark
