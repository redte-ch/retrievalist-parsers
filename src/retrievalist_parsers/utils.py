import itertools
import math
import os
from pathlib import Path
from typing import Generator, Iterable

from pdfminer.high_level import extract_pages
from pdfminer.layout import (
    LAParams,
    LTChar,
    LTTextContainer,
    LTTextLine,
    LTTextLineHorizontal,
)

DOCUMENT_EXTENSIONS = ("doc", "docx", "ppt", "pptx", "xls", "xlsx", "odt", "rtf")


def generate_characters(text_container: LTTextContainer):
    for container in text_container:
        if isinstance(container, LTChar):
            yield container
        elif isinstance(container, LTTextLine):
            for obj in container:
                if isinstance(obj, LTChar):
                    yield obj


def exclude_keys_from_dict(dict_obj, exclude_keys):
    return {key: value for key, value in dict_obj.items() if key not in exclude_keys}


def generate_words(text_container: LTTextContainer):
    characters = []
    for obj in generate_characters(text_container):
        character = obj.get_text()
        if character != " ":
            characters.append(character)
        else:
            word = "".join(characters).strip()
            if len(word) > 0:
                yield word
            characters.clear()
    if characters:
        yield "".join(characters)


def get_params_for_document_type():
    # disabling boxes_flow, as the style based hierarchy detection is based on
    # a purely flat list of paragraphs
    params = LAParams(boxes_flow=None, detect_vertical=False)  # setting for easy doc
    return params


def generate_text_elements(
    file_path: str, page_numbers=None
) -> Generator[LTTextContainer, None, None]:
    params = get_params_for_document_type()
    page_number = 0
    for page_layout in extract_pages(
        file_path, laparams=params, page_numbers=page_numbers
    ):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                element.meta = {"page": page_number}
                yield element
        page_number += 1


def truncate(number, decimals=0):
    """
    Returns a value truncated to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer.")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more.")
    elif decimals == 0:
        return math.trunc(number)

    factor = 10.0**decimals
    return math.trunc(number * factor) / factor


class DocumentTypeFilter:
    def __init__(self, endings=DOCUMENT_EXTENSIONS):
        self.endings = endings if isinstance(endings, (list, tuple)) else (endings,)

    def does_file_match(self, filename):
        return filename.split(".")[-1].lower() in self.endings


def closest_key(sorted_dict, key):
    "Return closest key in `sorted_dict` to given `key`."
    assert len(sorted_dict) > 0
    keys = list(itertools.islice(sorted_dict.irange(minimum=key), 1))
    keys.extend(itertools.islice(sorted_dict.irange(maximum=key, reverse=True), 1))
    return min(keys, key=lambda k: abs(key - k))


def find_file(
    root_dir: str, type_filter: DocumentTypeFilter, print_mod=10
) -> Iterable[Path]:
    processed = 0
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if type_filter.does_file_match(file):
                yield Path(root + "/" + file)
                processed += 1
                if print_mod and processed % print_mod == 0:
                    print("\nprocessed {}\n".format(processed))
    print("found {} file-paths".format(processed))


def head_char_line(container: LTTextLineHorizontal) -> LTChar:
    """
    :rtype LTChar
    :param container:
    :return:
    """
    for obj in container:
        if isinstance(obj, LTChar):
            return obj
