#include <iostream>
#include <fstream>
#include <string>
#include <unordered_set>
#include <cctype>
using namespace std;
int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: " << argv[0] << " <english_dict.txt>" << endl;
        return 1;
    }
    unordered_set<string> english_words;
    ifstream en_file(argv[1]);
    if (!en_file.is_open()) {
        cerr << "Could not open " << argv[1] << endl;
        return 1;
    }
    string word;
    while (en_file >> word) {
        string lower_word;
        for (char c : word) {
            lower_word += tolower(c);
        }
        english_words.insert(lower_word);
    }
    en_file.close();
    cerr << "Loaded " << english_words.size() << " English words." << endl;
    string line;
    while (getline(cin, line)) {
        if (line.empty()) continue;
        
        size_t space_pos = line.find(' ');
        string ne_word;
        if (space_pos != string::npos) {
            ne_word = line.substr(0, space_pos);
        } else {
            ne_word = line;
        }
        
        if (english_words.find(ne_word) == english_words.end()) {
            cout << line << "\n";
        }
    }
    return 0;
}
