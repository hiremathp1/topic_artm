#!/usr/bin/env python3
# Can be called as ./parser.py <filename>

import json


def get_text(obj):
    """Converts a json format transcription object to a string representing the actual text."""
    obj = obj["Items"]
    if "L" in obj:
        obj = obj["L"]

    def get_start_time(t):
        if "M" in t:
            return t["M"]["start_time"]["N"]
        return t["start_time"]

    def get_text(item):
        if "M" in item:
            item = item["M"]
        if isinstance(item["text"], dict) and "S" in item["text"]:
            return item["text"]["S"]
        return item["text"]

    # Sort text by start_time
    sorted_obj = sorted(obj, key=lambda x: get_start_time(x))
    return " ".join([get_text(item) for item in sorted_obj])


def parsefile(filename: str):
    return get_text(json.load(open(filename)))


if __name__ == "__main__":
    from sys import argv
    text = parsefile(argv[1])
    print(text)
    print("len:", len(text.split()))
