#!/usr/bin/env python3
import json
from dataclasses import dataclass, field
from typing import Dict, List

import spacy as spacy
from icecream import ic

spacy_core = "nl_core_news_lg"
text_store_path = 'data/1728-textstore.json'
annotation_store_path = 'data/1728-annotationstore-full.json'


@dataclass
class POSToken:
    word: str
    lemma: str
    pos: str


@dataclass
class Span:
    tag: str
    start_token_index: int
    end_token_index: int
    parameters: Dict[str, any] = field(default_factory=dict)


@dataclass
class BlackLabInputDocument:
    metadata: Dict[str, str] = field(default_factory=dict)
    tokens: List[POSToken] = field(default_factory=list)
    spans: List[Span] = field(default_factory=list)


def export(input_doc, path):
    print(f"- exporting to {path} ...", end="", flush=True)
    with open(path, "w") as f:
        f.write("DOC_START\n")
        for k, v in input_doc.metadata.items():
            f.write(f"  METADATA {k} {v}\n")
        f.write("  FIELD_START contents\n")

        number_of_tokens = len(input_doc.tokens)
        for i, token in enumerate(input_doc.tokens):
            f.write(f"    VAL word {token.word}\n")
            f.write(f"    VAL lemma {token.lemma}\n")
            f.write(f"    VAL pos {token.pos}\n")
            if i < number_of_tokens - 1:
                f.write("    ADVANCE 1\n")

        for span in input_doc.spans:
            f.write(f"    SPAN {span.tag} {span.start_token_index} {span.end_token_index}")
            for k, v in span.parameters.items():
                f.write(f" {k} {v}")
            f.write("\n")

        f.write("  FIELD_END\n")
        f.write("DOC_END\n")
    print()


def add_newline(l: str) -> str:
    return l if l.endswith("\n") else f"{l}\n"


def main():
    nlp = spacy.load(spacy_core)

    print(f"- reading {annotation_store_path} ...", end="", flush=True)
    with open(annotation_store_path) as f:
        annotations = json.load(f)
    print(f" {len(annotations)} annotations read.")
    line_annotations = [a for a in annotations if a["label"] == "lines"]
    line_ids = {}
    for la in line_annotations:
        line_idx = la["begin_anchor"]
        line_id = la["id"]
        line_ids[line_idx] = line_id

    print(f"- reading {text_store_path} ...", end="", flush=True)
    with open(text_store_path) as f:
        text_store = json.load(f)
        lines = text_store['_resources'][0]['_ordered_segments']
    print(f" {len(lines)} lines read.")
    fixed_lines = [l.replace("\n", " ") for l in lines]

    selection = fixed_lines  # [0:1000]
    # ic(selection)
    line_idx_for_ending_offset = {}
    offset = 0
    for i, line in enumerate([l for l in selection if l != "\n"]):
        offset += len(line) + 1
        line_idx_for_ending_offset[offset] = i
    text = ' '.join(selection)
    nlp.max_length = len(text)
    print(f"- spacy: processing {nlp.max_length} chars ...", end="", flush=True)
    doc = nlp(text)
    print()

    input_doc = BlackLabInputDocument()
    input_doc.metadata["title"] = "republic-1728"
    token_index = 0
    line_start = token_index
    anchor_number = 0
    # page_start = token_index
    for sentence in doc.sents:
        sentence_start = token_index
        for token in sentence:
            word = token.text.strip().strip('#')
            if word:
                pos_token = to_pos_token(input_doc, token, word)
                input_doc.tokens.append(pos_token)
                token_index += 1

            token_end_offset = token.idx + len(token.text_with_ws)
            token_is_last_of_line = token_end_offset in line_idx_for_ending_offset
            if token_is_last_of_line:  # last token of line
                line = " ".join([t.word for t in input_doc.tokens[line_start:token_index]])
                line_idx = line_idx_for_ending_offset[token_end_offset]
                input_doc.spans.append(
                    Span("l", line_start, token_index,
                         parameters={
                             "id": line_ids[line_idx],
                             # "line_idx": line_idx,
                             # "anchor_number": anchor_number,
                             # "text": line
                         }))

                # ic(line)
                # x = f"{line_ids[line_idx]} {line}"
                # ic(x)
                anchor_number += 1
                line_start = token_index

                # if token.text_with_ws == "\n":  # page ends
                #     input_doc.spans.append(Span("p", page_start, token_index - 1))
                #     page_start = token_index

        add_sentence_span(input_doc, sentence_start, token_index)
    # ic(input_doc)
    export(input_doc, "out/input.cif")


def add_sentence_span(input_doc, sentence_start, token_index):
    sentence_end = token_index
    if sentence_end > sentence_start:
        input_doc.spans.append(Span("s", sentence_start, sentence_end))
        # sent = " ".join([t.word for t in input_doc.tokens[sentence_start:sentence_end]])
        # ic(sent)


def to_pos_token(input_doc, token, word):
    lemma = token.lemma_.strip()
    if not lemma:
        ic(word)
        lemma = word
        ic(lemma)
    pos = token.pos_
    if not pos:
        raise Exception(
            f"lemma ({lemma}) or pos ({pos}) empty for word ({word}) after {input_doc.tokens[-3].word} {input_doc.tokens[-2].word} {input_doc.tokens[-1].word}")
    pos_token = POSToken(word=word, lemma=lemma, pos=pos)
    return pos_token


if __name__ == '__main__':
    main()
