from collections import Counter

from pdfminer.layout import LTTextBoxVertical

from retrievalist_parsers import utils
from retrievalist_parsers.analysis.styledistribution import StyleDistribution
from retrievalist_parsers.model.document import TextElement
from retrievalist_parsers.model.style import TextSize


def header_detector(element: TextElement, style_distribution: StyleDistribution):
    if isinstance(element._data, LTTextBoxVertical):
        return False
    stats = Counter()
    terms = element._data
    style = element.style

    if len(element.text) <= 2:
        return False

    # data tuple per line, element from pdfminer, annotated style info for whole line
    # todo, compute ratios over whole line // or paragraph :O
    if (
        (style.bold or style.italic)
        and style.mapped_font_size >= TextSize.middle
        or style.mapped_font_size > TextSize.middle
        or style.max_size > style_distribution.body_size + 2
    ):
        return check_valid_header_tokens(terms)
    else:
        return False


def check_valid_header_tokens(element):
    """
    fr a paragraph to be treated as a header, it has to contain at least 2 letters.
    @param element:
    @return:
    """
    alpha_count = 0
    numeric_count = 0
    for word in utils.generate_words(element):
        for c in word:
            if c.isalpha():
                alpha_count += 1
            if c.isnumeric():
                numeric_count += 1

            if alpha_count >= 2:
                return True
    return False
