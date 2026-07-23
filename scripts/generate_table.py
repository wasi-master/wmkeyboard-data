import gzip
import os
import langcodes
import struct
import humanize

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def get_counts(file_path):
    if not os.path.exists(file_path):
        return 0, 0, 0
    
    file_size = os.path.getsize(file_path)
    
    with open(file_path, 'rb') as f:
        f.seek(-4, 2)
        extracted_size = struct.unpack('<I', f.read(4))[0]
        
    line_count = 0
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        for _ in f:
            line_count += 1
            
    return file_size, extracted_size, line_count

def get_language_name(code):
    try:
        if code == "ze_en": return "Chinese (English input)"
        if code == "ze_zh": return "Chinese (Pinyin input)"
        name = langcodes.Language.get(code.replace('_', '-')).display_name()
        if "Unknown" in name:
            return code
        return name
    except Exception:
        return code

def format_size(num):
    if num == 0:
        return "-"
    return humanize.naturalsize(num, binary=False)

def format_count(num):
    if num == 0:
        return "-"
    return humanize.intcomma(num)

def main():
    languages = []
    
    # Check all subdirectories in data/
    for lang_code in sorted(os.listdir(DATA_DIR)):
        lang_dir = os.path.join(DATA_DIR, lang_code)
        if not os.path.isdir(lang_dir) or lang_code.startswith('.'):
            continue
            
        full_file = os.path.join(lang_dir, f"{lang_code}_full.txt.gz")
        offensive_file = os.path.join(lang_dir, f"{lang_code}_offensive.txt.gz")
        rom_file = os.path.join(lang_dir, f"{lang_code}_rom.txt.gz")
        
        full_size, full_ext_size, full_count = get_counts(full_file)
        offensive_size, off_ext_size, offensive_count = get_counts(offensive_file)
        rom_size, rom_ext_size, rom_count = get_counts(rom_file)
        
        lang_name = get_language_name(lang_code)
        
        languages.append({
            "name": lang_name,
            "code": lang_code,
            "full_size": full_size,
            "full_ext_size": full_ext_size,
            "full_count": full_count,
            "offensive_size": offensive_size,
            "off_ext_size": off_ext_size,
            "offensive_count": offensive_count,
            "rom_size": rom_size,
            "rom_ext_size": rom_ext_size,
            "rom_count": rom_count,
        })
    
    # Generate Markdown Table
    print("| Language Name | Language Code | Wordlist Size | Extracted Wordlist Size | Word Count | Profanity List Size | Extracted Profanity List Size | Profanity List Count | Romanized Wordlist Size | Extracted Romanized Wordlist Size | Romanized Wordlist Count |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    
    for lang in languages:
        row = [
            lang["name"],
            lang["code"],
            format_size(lang["full_size"]),
            format_size(lang["full_ext_size"]),
            format_count(lang["full_count"]),
            format_size(lang["offensive_size"]),
            format_size(lang["off_ext_size"]),
            format_count(lang["offensive_count"]),
            format_size(lang["rom_size"]),
            format_size(lang["rom_ext_size"]),
            format_count(lang["rom_count"]),
        ]
        print("| " + " | ".join(row) + " |")

if __name__ == "__main__":
    main()
