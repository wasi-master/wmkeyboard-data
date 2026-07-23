#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>
#include <sstream>

// Helper function to extract the first column of a CSV line,
// safely handling quoted strings that may contain commas.
std::string get_first_column(const std::string& line) {
    if (line.empty()) return "";

    // If the column is quoted
    if (line[0] == '"') {
        size_t end_quote = line.find('"', 1);
        while (end_quote != std::string::npos) {
            // Handle escaped double quotes ("") inside the string
            if (end_quote + 1 < line.length() && line[end_quote + 1] == '"') {
                end_quote = line.find('"', end_quote + 2);
            } else {
                return line.substr(1, end_quote - 1);
            }
        }
        return line.substr(1); // Fallback if no closing quote is found
    }

    // If the column is not quoted, just read up to the first comma
    size_t comma_pos = line.find(',');
    if (comma_pos != std::string::npos) {
        return line.substr(0, comma_pos);
    }

    return line;
}

int main() {
    std::ifstream file("./RomanUrdu_NLP_Sentiment-Corpus.csv");
    if (!file.is_open()) {
        std::cerr << "Error: Could not open input file." << std::endl;
        return 1;
    }

    std::string line;
    // Skip the header row (next(reader) equivalent)
    std::getline(file, line);

    // Dictionary equivalent for counting words
    std::unordered_map<std::string, int> word_counts;

    // Read the file line by line
    while (std::getline(file, line)) {
        std::string first_col = get_first_column(line);

        // Split the extracted text into words
        std::stringstream ss(first_col);
        std::string word;
        while (ss >> word) {
            word_counts[word]++;
        }
    }
    file.close();

    // Transfer map elements to a vector so they can be sorted
    std::vector<std::pair<std::string, int>> sorted_counts(word_counts.begin(), word_counts.end());

    // Sort by count (second element of the pair) in descending order
    std::sort(sorted_counts.begin(), sorted_counts.end(),
        [](const auto& a, const auto& b) {
            return a.second > b.second;
        });

    // Write the sorted counts to the output file
    std::ofstream outfile("ur_rom.txt");
    if (!outfile.is_open()) {
        std::cerr << "Error: Could not open output file." << std::endl;
        return 1;
    }

    for (const auto& pair : sorted_counts) {
        outfile << pair.first << " " << pair.second << "\n";
    }

    outfile.close();

    return 0;
}