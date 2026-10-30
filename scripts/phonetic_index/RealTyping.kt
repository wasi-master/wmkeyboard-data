import com.wasimaster.wmkeyboard.core.prediction.BengaliSuffixes
import com.wasimaster.wmkeyboard.core.prediction.DictionaryLoader
import com.wasimaster.wmkeyboard.core.prediction.MappedTrie
import com.wasimaster.wmkeyboard.core.prediction.PackedTrie
import com.wasimaster.wmkeyboard.core.prediction.PackedTrieCodec
import com.wasimaster.wmkeyboard.core.transliteration.AvroPhonetic
import com.wasimaster.wmkeyboard.core.transliteration.BengaliPhoneticIndex
import java.io.File
import java.text.Normalizer
import java.util.zip.GZIPInputStream
import kotlin.math.ln
import kotlin.math.min

// Replays SuggestionEngine.phoneticSuggestions over rows of real typing, with no user
// lexicon, picks or neural readings. Compile like build_phonetic_indexes.sh, adding
// BengaliSuffixes.kt. Input rows: prev2, prev, spelling, word, weight (TSV).
// args: flat ranked bundled en_bn bn_rom bigrams trigrams in.tsv out.tsv

fun readList(f: File) = GZIPInputStream(f.inputStream()).bufferedReader().useLines { ls ->
    ls.mapNotNull { val i = it.lastIndexOf(' '); if (i <= 0) null else it.substring(0, i) to it.substring(i + 1).toInt() }.toList()
}
fun viaTrie(e: List<Pair<String, Int>>): List<Pair<String, Int>> {
    val f = File.createTempFile("real", ".wmdict"); f.deleteOnExit()
    f.outputStream().use { PackedTrieCodec.write(PackedTrie.of(e), it) }
    return MappedTrie.open(f)!!.entries()
}
fun key(w: String) = Normalizer.normalize(w.lowercase(), Normalizer.Form.NFC)
fun pre(w: String) = w.replace("ড়", "ড়").replace("ঢ়", "ঢ়").replace("য়", "য়")

class Pack(bi: File, tri: File) {
    val bigrams = HashMap<String, Int>(300_000)
    val trigrams = HashMap<String, Int>(150_000)
    init {
        fun read(f: File, cap: Int, into: HashMap<String, Int>) {
            GZIPInputStream(f.inputStream()).bufferedReader().useLines { ls ->
                var n = 0
                for (l in ls) {
                    if (n++ >= cap) break
                    val i = l.lastIndexOf(' '); if (i <= 0) continue
                    into[l.substring(0, i).split(' ').joinToString(" ") { key(it) }] = l.substring(i + 1).toInt()
                }
            }
        }
        read(bi, 150_000, bigrams); read(tri, 75_000, trigrams)
    }
    // The engine's contextCount with no user lexicon: pack counts / PACK_COUNT_SCALE.
    fun count(prev: String, prev2: String?, c: String): Int = maxOf(
        (bigrams["${key(prev)} ${key(c)}"] ?: 0) / 50,
        if (prev2 != null) (trigrams["${key(prev2)} ${key(prev)} ${key(c)}"] ?: 0) * 2 / 50 else 0,
    )
}

fun main(a: Array<String>) {
    val flat = viaTrie(readList(File(a[0])))
    val ranked = viaTrie(readList(File(a[1])))
    val bundled = viaTrie(File(a[2]).inputStream().use { DictionaryLoader.loadEntries(it) })
    val map = HashMap<String, MutableList<String>>()
    for (f in listOf(a[3], a[4])) File(f).forEachLine { line ->
        val t = line.trim(); val tab = t.indexOf('\t')
        if (t.isNotEmpty() && !t.startsWith("#") && tab > 0) {
            val k = t.substring(0, tab).trim().lowercase(); val v = t.substring(tab + 1).trim()
            if (k.isNotEmpty() && v.isNotEmpty()) map.getOrPut(k) { mutableListOf() }.let { if (v !in it) it.add(v) }
        }
    }
    val pack = Pack(File(a[5]), File(a[6]))
    val today = BengaliPhoneticIndex(BengaliPhoneticIndex.withBundledRanking(flat) { bundled })
    val fresh = BengaliPhoneticIndex(BengaliPhoneticIndex.withBundledRanking(ranked) { bundled })

    fun inContext(words: List<String>, prev: String?, prev2: String?): List<String> {
        if (words.size < 2 || prev.isNullOrEmpty()) return words
        val head = words.take(6)
        val boosts = head.map { val c = pack.count(prev, prev2, it); if (c > 0) min(ln(1.0 + 0.5 * ln(1.0 + c)), ln(4.0)) else 0.0 }
        if (boosts.all { it == 0.0 }) return words
        val order = head.indices.sortedWith(compareByDescending<Int> { boosts[it] - it * 0.25 }.thenBy { it })
        return order.map { head[it] } + words.drop(6)
    }
    fun readings(ix: BengaliPhoneticIndex, useMap: Boolean, r: String, prev: String?, prev2: String?): List<String> {
        val listed = if (useMap) inContext(map[r].orEmpty(), prev, prev2) else emptyList()
        val ordered = LinkedHashSet(listed)
        val lit = AvroPhonetic.transliterate(r)
        val sib = ix.lookup(r)
        val litF = ix.frequencyOf(lit)
        val topF = sib.firstOrNull()?.let(ix::frequencyOf) ?: 0
        if (litF > 0 && topF < litF * 2.0) ordered.add(lit)
        ordered.addAll(sib)
        BengaliSuffixes.join(r, { s ->
            (if (useMap) map[s]?.firstOrNull() else null) ?: ix.lookup(s).firstOrNull()
                ?: AvroPhonetic.transliterate(s).takeIf { ix.frequencyOf(it) > 0 }
        }, AvroPhonetic::transliterate).forEach(ordered::add)
        ordered.add(lit)
        val rest = inContext(ordered.filterNot(listed.toSet()::contains), prev, prev2)
        return listed + rest
    }

    File(a[8]).bufferedWriter().use { w ->
        File(a[7]).bufferedReader().useLines { ls ->
            for (l in ls) {
                val p = l.split('\t'); if (p.size < 5) continue
                val prev2 = p[0].ifEmpty { null }; val prev = p[1].ifEmpty { null }
                val r = p[2]; val gold = pre(p[3])
                val cols = ArrayList<String>()
                fun rank(x: List<String>): Int = x.map(::pre).indexOf(gold)
                // rank of the gold word in: today, new, new+map, new+map+context (-1 = absent)
                cols += rank(readings(today, false, r, null, null)).toString()
                cols += rank(readings(fresh, false, r, null, null)).toString()
                cols += rank(readings(today, true, r, null, null)).toString()
                cols += rank(readings(fresh, true, r, null, null)).toString()
                val full = readings(fresh, true, r, prev, prev2)
                cols += rank(full).toString()
                val known = fresh.frequencyOf(p[3]) > 0 || fresh.frequencyOf(gold) > 0
                val sameKey = BengaliPhoneticIndex.foldRoman(r) == BengaliPhoneticIndex.foldBengali(p[3])
                w.write(listOf(r, p[3], p[4], cols.joinToString(","), if (known) "1" else "0", if (sameKey) "1" else "0", full.firstOrNull() ?: "", if (r in map) "1" else "0").joinToString("\t"))
                w.write("\n")
            }
        }
    }
}
