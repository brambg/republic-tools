#!/usr/bin/env python3
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any

import spacy as spacy
from loguru import logger

spacy_core = "nl_core_news_lg"
text_store_path = 'data/1728-textstore-220718.json'
annotation_store_path = 'data/1728-annotationstore-220718.json'


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


class ComplexHandler(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, POSToken) or isinstance(o, BlackLabInputDocument) or isinstance(o, Span):
            return o.__dict__
        else:
            return json.JSONEncoder.default(self, o)


@logger.catch
def main():
    nlp = spacy.load(spacy_core)

    annotations, line_ids = load_annotations()

    lines = load_text_lines()
    fixed_lines = [l.replace("\n", " ") for l in lines]

    selection = fixed_lines  # [0:1000]
    # ic(selection)
    line_idx_for_ending_offset = index_line_ending_offset(selection)

    doc = calculate_pos(nlp, selection)

    input_doc = init_input_doc()

    token_index = 0
    line_start = token_index
    anchor_number = 0
    token_spans_per_anchor = {}
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
                token_spans_per_anchor[anchor_number] = (line_start, token_index)
                anchor_number += 1
                line_start = token_index

                # if token.text_with_ws == "\n":  # page ends
                #     input_doc.spans.append(Span("p", page_start, token_index - 1))
                #     page_start = token_index

        add_sentence_span(input_doc, sentence_start, token_index)

    add_annotation_spans(input_doc, annotations, token_spans_per_anchor)
    # ic(input_doc)
    export(input_doc, "out/input.cif")
    export_json(input_doc)


def init_input_doc():
    input_doc = BlackLabInputDocument()
    input_doc.metadata["title"] = "republic-1728"
    input_doc.metadata["text_source"] = text_store_path
    input_doc.metadata["annotation_source"] = annotation_store_path
    return input_doc


def add_annotation_spans(input_doc, annotations, token_spans_per_anchor):
    add_spans(annotations=annotations, input_doc=input_doc, token_spans_per_anchor=token_spans_per_anchor,
              annotation_type="attendant", span_tag="attendant", parameter_func=lambda a: a["metadata"])

    add_spans(annotations=annotations, input_doc=input_doc, token_spans_per_anchor=token_spans_per_anchor,
              annotation_type="session", span_tag="session", parameter_func=session_parameters)

    add_spans(annotations=annotations, input_doc=input_doc, token_spans_per_anchor=token_spans_per_anchor,
              annotation_type="republic_paragraph", span_tag="paragraph", parameter_func=paragraph_parameters)

    add_spans(annotations=annotations, input_doc=input_doc, token_spans_per_anchor=token_spans_per_anchor,
              annotation_type="attendance_list", span_tag="attendance_list", parameter_func=attendance_list_parameters)

    add_spans(annotations=annotations, input_doc=input_doc, token_spans_per_anchor=token_spans_per_anchor,
              annotation_type="page", span_tag="page", parameter_func=lambda a: {"scan_id": a["metadata"]["scan_id"]})

    add_spans(annotations=annotations, input_doc=input_doc, token_spans_per_anchor=token_spans_per_anchor,
              annotation_type="resolution", span_tag="resolution", parameter_func=resolution_parameters)


def calculate_pos(nlp, selection):
    text = ' '.join(selection)
    nlp.max_length = len(text)
    logger.info(f"spacy: processing {nlp.max_length} chars ...")
    doc = nlp(text)
    return doc


def index_line_ending_offset(selection):
    line_idx_for_ending_offset = {}
    offset = 0
    for i, line in enumerate([l for l in selection if l != "\n"]):
        offset += len(line) + 1
        line_idx_for_ending_offset[offset] = i
    return line_idx_for_ending_offset


def load_text_lines():
    logger.info(f"reading {text_store_path} ...")
    with open(text_store_path) as f:
        text_store = json.load(f)
        lines = text_store['_resources'][0]['_ordered_segments']
    logger.info(f" {len(lines)} lines read.")
    return lines


def load_annotations():
    logger.info(f"reading {annotation_store_path} ...")
    with open(annotation_store_path) as f:
        annotations = json.load(f)
    logger.info(f" {len(annotations)} annotations read.")
    line_annotations = [a for a in annotations if a["type"] == "line"]
    line_ids = {}
    for la in line_annotations:
        line_idx = la["begin_anchor"]
        line_id = la["id"]
        line_ids[line_idx] = line_id
    return annotations, line_ids


def export_json(input_doc):
    path = 'out/out.json'
    logger.info(f"writing to {path}")
    with open(path, "w") as f:
        json.dump(obj=input_doc, fp=f, indent=4, cls=ComplexHandler)


def export(input_doc, path):
    logger.info(f"exporting to {path} ...")
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
                if isinstance(v, str):
                    value = v.replace(" ", "_").replace("#", "_")
                else:
                    value = v
                if value != "":
                    f.write(f" {k} {value}")
            f.write("\n")

        f.write("  FIELD_END\n")
        f.write("DOC_END\n")


def add_newline(l: str) -> str:
    return l if l.endswith("\n") else f"{l}\n"


def add_spans(annotations, input_doc, token_spans_per_anchor, annotation_type, span_tag, parameter_func):
    attendant_annotations = [a for a in annotations if a["type"] == annotation_type]
    logger.info(f"{len(annotations)} {annotation_type} annotations found")
    for annotation in attendant_annotations:
        annotation_id = annotation["id"]
        begin_anchor = annotation["begin_anchor"]
        end_anchor = annotation["end_anchor"]
        if begin_anchor in token_spans_per_anchor and end_anchor in token_spans_per_anchor:
            start_token = token_spans_per_anchor[begin_anchor][0]
            end_token = token_spans_per_anchor[end_anchor][1]
            parameters = parameter_func(annotation)
            parameters["id"] = annotation_id
            input_doc.spans.append(
                Span(span_tag, start_token, end_token, parameters=parameters))
        else:
            if begin_anchor not in token_spans_per_anchor:
                logger.warning(f"begin_anchor {begin_anchor} not a key"
                               f" in token_spans_per_anchor, no {span_tag} span added!")
            if end_anchor not in token_spans_per_anchor:
                logger.warning(f"end_anchor {end_anchor} not a key"
                               f" in token_spans_per_anchor, no {span_tag} span added!")


def session_parameters(annotation: Dict[str, Any]) -> Dict[str, Any]:
    parameters = annotation["metadata"]
    parameters.pop("resolution_ids")
    parameters.pop("text_page_num")
    return parameters


def attendance_list_parameters(annotation: Dict[str, Any]) -> Dict[str, Any]:
    parameters = annotation["metadata"]
    parameters.pop("text_page_num")
    return parameters


def resolution_parameters(annotation: Dict[str, Any]) -> Dict[str, Any]:
    parameters = annotation["metadata"]
    parameters.pop("text_page_num")
    parameters.pop("proposition_origin")
    return parameters


def paragraph_parameters(annotation: Dict[str, Any]) -> Dict[str, Any]:
    parameters = annotation["metadata"]
    parameters.pop("text_page_num")
    parameters.pop("page_num")
    return parameters


def add_sentence_span(input_doc, sentence_start, token_index):
    sentence_end = token_index
    if sentence_end > sentence_start:
        input_doc.spans.append(Span("s", sentence_start, sentence_end))
        # sent = " ".join([t.word for t in input_doc.tokens[sentence_start:sentence_end]])
        # ic(sent)


def to_pos_token(input_doc, token, word):
    lemma = token.lemma_.strip()
    if not lemma:
        logger.warning(f"no lemma found, using {word}")
        lemma = word
    pos = token.pos_
    if not pos:
        raise Exception(
            f"lemma ({lemma}) or pos ({pos}) empty for word ({word}) after {input_doc.tokens[-3].word} {input_doc.tokens[-2].word} {input_doc.tokens[-1].word}")
    pos_token = POSToken(word=word, lemma=lemma, pos=pos)
    return pos_token


if __name__ == '__main__':
    main()
