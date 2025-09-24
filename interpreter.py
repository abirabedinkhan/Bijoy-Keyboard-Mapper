import json
from converter import Unicode

# Load the JSON file
with open("bijoyClassic_parsed.json", "r", encoding="utf-8") as f:
    data = json.load(f)

key_map = data["map"]["general"]

def map_input_string(input_string, key_mapping):
    output = []
    i = 0
    while i < len(input_string):
        # Try 3-character lookahead
        if i + 2 < len(input_string) and input_string[i:i+3] in key_mapping:
            output.append(key_mapping[input_string[i:i+3]])
            i += 3
        elif i + 1 < len(input_string) and input_string[i:i+2] in key_mapping:
            output.append(key_mapping[input_string[i:i+2]])
            i += 2
        elif input_string[i] in key_mapping:
            output.append(key_mapping[input_string[i]])
            i += 1
        else:
            output.append(input_string[i])  # Fallback: use original character
            i += 1
    return ''.join(output)


def interpreter(input_string): 
    unicode = Unicode()
    return unicode.convertBijoyToUnicode(map_input_string(input_string, key_map))
