#!/usr/bin/env python3
from dataclasses import dataclass, field
from typing import Dict, List

import spacy as spacy
from icecream import ic

spacy_core = "nl_core_news_lg"
input_file = 'data/1728-textstore.txt'


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


@dataclass
class BlackLabInputDocument:
    metadata: Dict[str, str] = field(default_factory=dict)
    tokens: List[POSToken] = field(default_factory=list)
    spans: List[Span] = field(default_factory=list)


def export(input_doc, path):
    print(f"exporting to {path}")
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
            f.write(f"    SPAN {span.tag} {span.start_token_index} {span.end_token_index}\n")

        f.write("  FIELD_END\n")
        f.write("DOC_END\n")


def main():
    nlp = spacy.load(spacy_core)
    with open(input_file) as f:
        lines = f.readlines()
    selection = lines
    ic(selection)
    text = ' '.join(selection)
    nlp.max_length = len(text)
    doc = nlp(text)

    input_doc = BlackLabInputDocument()
    input_doc.metadata["title"] = "republic-1728"
    token_index = 0
    line_start = token_index
    for sentence in doc.sents:
        sentence_start = token_index
        for token in sentence:
            word = token.text.strip()
            if word:
                pos_token = POSToken(word=word, lemma=token.lemma_.strip(), pos=token.pos_)
                input_doc.tokens.append(pos_token)
                token_index += 1
            else:  # token was all whitespace -> line ending
                input_doc.spans.append(Span("l", line_start, token_index))
                line = " ".join([t.word for t in input_doc.tokens[line_start:token_index]])
                ic(line)
                line_start = token_index

        sentence_end = token_index
        if sentence_end > sentence_start:
            input_doc.spans.append(Span("s", sentence_start, sentence_end))
            sent = " ".join([t.word for t in input_doc.tokens[sentence_start:sentence_end]])
            ic(sent)
    # ic(input_doc)
    export(input_doc, "out/input.cif")


if __name__ == '__main__':
    main()
