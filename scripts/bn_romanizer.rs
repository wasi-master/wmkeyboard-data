use serde::Deserialize;
use std::collections::{HashMap, HashSet};
use std::fs::File;
use std::io::{self, BufRead, BufReader, BufWriter, Write};

#[derive(Deserialize)]
struct Record {
    anchor: String,
    positive: String,
    negative: String,
}

fn main() -> io::Result<()> {
    let en_dict_path = "en.txt";
    let jsonl_path = "banglish_pairs_filtered.jsonl";
    let output_path = "bn_rom.txt";

    // 1. Load the English dictionary into a HashSet
    let mut en_words = HashSet::new();
    if let Ok(file) = File::open(en_dict_path) {
        for line in BufReader::new(file).lines().map_while(Result::ok) {
            en_words.insert(line.trim().to_lowercase());
        }
        println!("Loaded {} English words.", en_words.len());
    } else {
        eprintln!("Warning: Could not open {}. Make sure it exists.", en_dict_path);
    }

    // 2. Process the JSONL file and count Banglish words
    let mut word_counts: HashMap<String, usize> = HashMap::new();

    let json_file = File::open(jsonl_path).expect("Failed to open JSONL file");
    let reader = BufReader::new(json_file);

    for (line_num, line) in reader.lines().enumerate() {
        let line = line?;

        if line.trim().is_empty() {
            continue;
        }

        match serde_json::from_str::<Record>(&line) {
            Ok(record) => {
                let combined_text = format!("{} {} {}", record.anchor, record.positive, record.negative);

                let clean_text = combined_text.replace(|c: char| !c.is_ascii_alphabetic(), " ");

                for word in clean_text.split_whitespace() {
                    let lower_word = word.to_lowercase();

                    if lower_word.len() > 1 && !en_words.contains(&lower_word) {
                        *word_counts.entry(lower_word).or_insert(0) += 1;
                    }
                }
            }
            Err(e) => {
                eprintln!("Failed to parse line {}: {}", line_num + 1, e);
            }
        }
    }

    // 3. Sort the words by frequency (descending), then alphabetically (ascending)
    let mut sorted_counts: Vec<(String, usize)> = word_counts.into_iter().collect();
    sorted_counts.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));

    // 4. Write out to the result file
    let out_file = File::create(output_path)?;
    let mut writer = BufWriter::new(out_file);

    // Iterating over a reference (&) prevents moving the vector
    for (word, count) in &sorted_counts {
        writeln!(writer, "{} {}", word, count)?;
    }

    println!("Successfully wrote {} Banglish words to {}", sorted_counts.len(), output_path);

    Ok(())
}