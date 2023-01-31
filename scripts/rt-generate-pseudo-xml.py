#!/usr/bin/env python3
import json
from collections import defaultdict


def main():
    with open('out/out.json') as f:
        data = json.load(f)
    tokens = data["tokens"]
    spans = data["spans"]
    open_tags = defaultdict(lambda: [])
    close_tags = defaultdict(lambda: [])
    for s in spans:
        open_tags[s["start_token_index"]].append(f"<{s['tag']}>")
        close_tags[s["end_token_index"]].append(f"</{s['tag']}>")
    for i, token in enumerate(tokens):
        if i in open_tags:
            tags = sorted(open_tags[i])
            if "<l>" in tags:
                print(f"{i:6d} | ", end="")
            print("".join(tags), end="")
        print(f"{token['word']}", end="")
        if i + 1 in close_tags:
            tags = sorted(close_tags[i + 1], reverse=True)
            print("".join(tags), end="")
            if "</l>" in tags:
                print()
            else:
                print(" ", end="")
        else:
            print(" ", end="")
    print()


if __name__ == '__main__':
    main()
