#!/usr/bin/env bash
# Rebuilds data/<lang>/<lang>_phonetic_v<format>r<fold>.wmpi.gz, the phonetic
# index WM Keyboard folds over data/<lang>/<lang>_full.txt.gz (Bangla's over
# bn_full_v2.txt.gz, the list with corpus counts), for every
# language whose index is a table (wasi-master/wmkeyboard#716).
#
# Compiles WM Keyboard's own fold code (core/language transliteration) and its
# own trie (core/prediction) with kotlinc, so each table is exactly what the app
# would build on a phone over the same download. The fold code calls the app's
# Rust engine, so its host library is built first (needs cargo).
#
# Bangla's table carries the ranking of the app's bundled list
# (app/dictionaries-src/bn.txt), so it is rebuilt when that changes too, under
# the new name the app's bumped BengaliPhoneticIndex.REVISION gives it.
#
# Rerun whenever a <lang>_full.txt.gz changes. When the app bumps
# PhoneticTableBuilder.VERSION or a fold's REVISION the file name changes too:
# the new tables are written beside the old ones, which stay for the app
# versions that still fetch them.
#
#   scripts/build_phonetic_indexes.sh [path/to/WMKeyboard] [lang...]
#
# Needs kotlinc and a JDK. KOTLINC and JAVA_HOME override where they are
# looked for; Android Studio's bundled copies are the macOS default.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$(cd "${1:-$ROOT/../WMKeyboard}" && pwd)"
shift || true
LANGS=("$@")
if [ ${#LANGS[@]} -eq 0 ]; then
    LANGS=(hi ur mr gu pa or ta te kn ml fa ar bn as)
fi
STUDIO="/Applications/Android Studio.app/Contents"
KOTLINC="${KOTLINC:-$STUDIO/plugins/Kotlin/kotlinc}"
export JAVA_HOME="${JAVA_HOME:-$STUDIO/jbr/Contents/Home}"
SRC="$APP/core/language/src/main/java/com/wasimaster/wmkeyboard/core/transliteration"
TRIE="$APP/core/prediction/src/main/java/com/wasimaster/wmkeyboard/core/prediction"

"$APP/native/wm-engine-jni/build-host.sh" >&2
case "$(uname -s)" in
    Darwin) LIB="$APP/native/wm-engine-jni/target/release/libwm_engine_jni.dylib" ;;
    *) LIB="$APP/native/wm-engine-jni/target/release/libwm_engine_jni.so" ;;
esac

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# Khipro's spec files are fetched on the phone (Android and coroutines), and no
# fold reads Khipro, so its three files stay out. The JNI loaders live in
# core/language's engine package and core/prediction's PredictionNative.
ENGINE="$APP/core/language/src/main/java/com/wasimaster/wmkeyboard/core/engine"
SOURCES=()
for f in "$SRC"/*.kt; do
    case "$(basename "$f")" in
        Khipro.kt | KhiproRomanizer.kt | KhiproSpecs.kt) ;;
        *) SOURCES+=("$f") ;;
    esac
done
"$KOTLINC/bin/kotlinc" -nowarn -d "$WORK/classes" \
    "${SOURCES[@]}" "$ENGINE/NativeEngine.kt" "$ENGINE/NativeHandles.kt" \
    "$TRIE/Trie.kt" "$TRIE/TrieWalker.kt" "$TRIE/TrieCompleter.kt" "$TRIE/PackedTrie.kt" \
    "$TRIE/PackedTrieCodec.kt" "$TRIE/RankFloorCache.kt" "$TRIE/MappedTrie.kt" "$TRIE/DictionaryLoader.kt" \
    "$TRIE/PredictionNative.kt" \
    "$ROOT/scripts/phonetic_index/PhoneticIndexTables.kt"
"$JAVA_HOME/bin/java" -Xmx6g -Dwmkeyboard.engine.lib="$LIB" -Dwmkeyboard.app="$APP" \
    -cp "$WORK/classes:$KOTLINC/lib/kotlin-stdlib.jar" PhoneticIndexTablesKt \
    "$ROOT/data" "${LANGS[@]}"
