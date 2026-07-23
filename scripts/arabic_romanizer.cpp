#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>

using namespace std;

int get_utf8_len(unsigned char c) {
    if ((c & 0x80) == 0) return 1;
    if ((c & 0xE0) == 0xC0) return 2;
    if ((c & 0xF0) == 0xE0) return 3;
    if ((c & 0xF8) == 0xF0) return 4;
    return 1; // fallback
}

bool is_arabic_char(const string& text, size_t i, int len) {
    unsigned char c = text[i];
    if (len == 2) {
        if (c >= 0xD8 && c <= 0xDF) return true;
    } else if (len == 3) {
        if (c == 0xE0) {
            unsigned char c2 = text[i+1];
            if (c2 >= 0xA2 && c2 <= 0xA3) return true; // 08A0 - 08FF
        } else if (c == 0xEF) {
            unsigned char c2 = text[i+1];
            if (c2 >= 0xAD && c2 <= 0xB7) return true; // FB50 - FDFF
            if (c2 >= 0xB9 && c2 <= 0xBB) return true; // FE70 - FEFF
        }
    }
    return false;
}

bool is_ascii_punct_or_space(unsigned char c) {
    if (c <= 32) return true;
    if (c >= 33 && c <= 47 && c != '-' && c != '\'') return true;
    if (c >= 58 && c <= 64) return true;
    if (c >= 91 && c <= 96) return true;
    if (c >= 123 && c <= 126) return true;
    return false;
}

void extract_words(const string& text, unordered_map<string, int>& word_counts) {
    string current_word = "";
    
    for (size_t i = 0; i < text.length(); ) {
        unsigned char c = text[i];
        int len = get_utf8_len(c);
        
        if (i + len > text.length()) {
            len = text.length() - i;
        }
        
        if (len > 1) {
            if (is_arabic_char(text, i, len)) {
                if (!current_word.empty()) {
                    while (!current_word.empty() && (current_word.back() == '\'' || current_word.back() == '-')) current_word.pop_back();
                    if (!current_word.empty()) { word_counts[current_word]++; current_word = ""; }
                }
            } else {
                if (len == 2 && c == 0xC3 && text[i+1] >= 0x80 && text[i+1] <= 0x9E) {
                    current_word += (char)c;
                    current_word += (char)(text[i+1] + 0x20);
                } else {
                    for (int j = 0; j < len; j++) current_word += text[i+j];
                }
            }
            i += len;
            continue;
        }
        
        if (is_ascii_punct_or_space(c)) {
            if (!current_word.empty()) {
                while (!current_word.empty() && (current_word.back() == '\'' || current_word.back() == '-')) current_word.pop_back();
                if (!current_word.empty()) { word_counts[current_word]++; current_word = ""; }
            }
            i++;
            continue;
        }
        
        if (c == '-' || c == '\'') {
            if (!current_word.empty()) {
                current_word += (char)c;
            }
            i++;
            continue;
        }
        
        if (c >= 'A' && c <= 'Z') c += 32;
        
        current_word += (char)c;
        i++;
    }
    
    if (!current_word.empty()) {
        while (!current_word.empty() && (current_word.back() == '\'' || current_word.back() == '-')) current_word.pop_back();
        if (!current_word.empty()) { word_counts[current_word]++; }
    }
}

int main() {
    ifstream fin("ELNER-DZ.json");
    if (!fin) {
        cerr << "Failed to open ELNER-DZ.json" << endl;
        return 1;
    }
    
    unordered_map<string, int> word_counts;
    string line;
    
    cout << "Parsing..." << endl;
    
    while (getline(fin, line)) {
        size_t pos = line.find("\"text\": \"");
        if (pos != string::npos) {
            size_t start = pos + 9;
            string text_val = "";
            bool escaped = false;
            for (size_t i = start; i < line.length(); ++i) {
                if (escaped) {
                    if (line[i] == 'n' || line[i] == 'r' || line[i] == 't') text_val += ' ';
                    else text_val += line[i];
                    escaped = false;
                } else if (line[i] == '\\') {
                    escaped = true;
                } else if (line[i] == '"') {
                    break;
                } else {
                    text_val += line[i];
                }
            }
            extract_words(text_val, word_counts);
        }
    }
    
    cout << "Sorting " << word_counts.size() << " unique words..." << endl;
    
    vector<pair<string, int>> sorted_words(word_counts.begin(), word_counts.end());
    sort(sorted_words.begin(), sorted_words.end(), [](const pair<string, int>& a, const pair<string, int>& b) {
        if (a.second != b.second) return a.second > b.second;
        return a.first < b.first;
    });
    
    cout << "Writing to ar_rom.txt..." << endl;
    
    ofstream fout("ar_rom.txt");
    for (const auto& p : sorted_words) {
        fout << p.first << " " << p.second << "\n";
    }
    
    cout << "Done!" << endl;
    return 0;
}
