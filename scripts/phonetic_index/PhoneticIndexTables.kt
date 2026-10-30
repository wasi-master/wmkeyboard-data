// Writes data/<lang>/<lang>_phonetic_v<format>r<fold>.wmpi.gz: the phonetic
// index WM Keyboard folds over data/<lang>/<lang>_full.txt.gz, built ahead of
// time so the keyboard maps it instead of folding the whole list at every
// start (wasi-master/wmkeyboard#716). Built by scripts/build_phonetic_indexes.sh
// against WM Keyboard's own fold code (PhoneticTables) and its own trie, so the
// table is byte for byte what the app would build over the same download.
//
// Bangla's list is flat, so the app lays the ranking of its own bundled list
// (app/dictionaries-src/bn.txt) over it before filing it; so does this, reading
// that list from the app checkout named by -Dwmkeyboard.app.
//
//   PhoneticIndexTablesKt <data dir> <lang>...
import com.wasimaster.wmkeyboard.core.prediction.DictionaryLoader
import com.wasimaster.wmkeyboard.core.prediction.MappedTrie
import com.wasimaster.wmkeyboard.core.prediction.PackedTrie
import com.wasimaster.wmkeyboard.core.prediction.PackedTrieCodec
import com.wasimaster.wmkeyboard.core.transliteration.BengaliPhoneticIndex
import com.wasimaster.wmkeyboard.core.transliteration.PackedPhoneticTable
import com.wasimaster.wmkeyboard.core.transliteration.PhoneticTables
import java.io.File
import java.util.zip.GZIPInputStream
import java.util.zip.GZIPOutputStream

// The app's WordlistDownloadManager.parse, for a FREQUENCY list read whole
// (the ALL tier): the same floor, the same length cap, the same flat-list rule.
private const val MIN_FREQUENCY = 2
private const val MAX_WORD_LENGTH = 48

private fun parse(list: File): Pair<Array<String?>, IntArray> {
    val words = ArrayList<String>()
    val frequencies = ArrayList<Int>()
    var ranked: Boolean? = null
    GZIPInputStream(list.inputStream(), 64 * 1024).bufferedReader().useLines { lines ->
        for (line in lines) {
            val trimmed = line.trim()
            if (trimmed.isEmpty() || trimmed.startsWith("#")) continue
            val separator = trimmed.lastIndexOf(' ')
            if (separator <= 0) continue
            val word = trimmed.substring(0, separator).trim()
            val frequency = trimmed.substring(separator + 1).toIntOrNull() ?: continue
            if (ranked == null) ranked = frequency >= MIN_FREQUENCY
            if (ranked == true && frequency < MIN_FREQUENCY) break
            if (word.length > MAX_WORD_LENGTH || ' ' in word) continue
            words += word
            frequencies += frequency
        }
    }
    return words.toTypedArray<String?>() to frequencies.toIntArray()
}

/** [words] through the app's trie and back, the way a list reaches the phone's index. */
private fun throughTrie(lang: String, words: Array<String?>, frequencies: IntArray): MappedTrie {
    val trie = PackedTrie.of(words, frequencies, words.size)
    val packed = File.createTempFile("phonetic-$lang", ".wmdict")
    packed.deleteOnExit()
    packed.outputStream().use { PackedTrieCodec.write(trie, it) }
    return requireNotNull(MappedTrie.open(packed)) { "$lang: the trie does not read back" }
}

/**
 * The app's bundled Bangla list as the keyboard reads it: compiled the way
 * dictc compiles it into the APK, then mapped.
 */
private fun bundledBangla(): List<Pair<String, Int>> {
    val app = File(requireNotNull(System.getProperty("wmkeyboard.app")) { "-Dwmkeyboard.app is not set" })
    val entries = File(app, "app/dictionaries-src/bn.txt").inputStream().use { DictionaryLoader.loadEntries(it) }
    val packed = File.createTempFile("phonetic-bn-bundled", ".wmdict")
    packed.deleteOnExit()
    packed.outputStream().use { PackedTrieCodec.write(PackedTrie.of(entries), it) }
    return requireNotNull(MappedTrie.open(packed)) { "bn: the bundled list does not read back" }.entries()
}

/**
 * The list [lang]'s table is filed over, the one the app's catalog downloads:
 * Bangla's counted `bn_full_v2` since table revision 2, `<lang>_full` elsewhere.
 */
private fun listName(lang: String): String = if (lang == "bn") "bn_full_v2.txt.gz" else "${lang}_full.txt.gz"

fun main(args: Array<String>) {
    val data = File(args[0])
    for (lang in args.drop(1)) {
        val list = File(data, "$lang/${listName(lang)}")
        // Through the app's own trie and back, as a download goes: the trie
        // merges duplicates and snaps frequencies, and the index is filed from
        // what the trie hands back, in its order.
        val (words, frequencies) = parse(list)
        val mapped = throughTrie(lang, words, frequencies)
        val listed = mapped.entries()
        val entries = if (lang == "bn") BengaliPhoneticIndex.withBundledRanking(listed, ::bundledBangla) else listed
        val out = File(data, "$lang/${PhoneticTables.publishedName(lang)}")
        val inflated = File.createTempFile("phonetic-$lang", ".wmpi")
        inflated.outputStream().buffered().use { PhoneticTables.write(lang, entries, it, lang, mapped.wordCount) }
        val table = requireNotNull(PackedPhoneticTable.open(inflated)) { "$lang: the table does not read back" }
        check(PhoneticTables.fits(lang, table) && table.sourceWords == mapped.wordCount && table.sourceTag == lang)
        GZIPOutputStream(out.outputStream(), 64 * 1024).use { gz -> inflated.inputStream().use { it.copyTo(gz) } }
        System.err.println("$lang: ${mapped.wordCount} words, ${inflated.length()} bytes, ${out.length()} gzipped -> ${out.name}")
        inflated.delete()
    }
}
