import statistics
from collections import Counter

from pdfminer.layout import LTChar, LTTextBoxHorizontal

from retrievalist_parsers.analysis.sizemapper import SizeMapper
from retrievalist_parsers.analysis.styledistribution import StyleDistribution
from retrievalist_parsers.model.document import TextElement
from retrievalist_parsers.model.style import Style, TextSize
from retrievalist_parsers.utils import truncate


class StyleAnnotator:
    """
    creates a PdfElements from incoming pdf-paragraphs (raw LTTextContainer from pdfminer.six).
    - annotates paragraph with @Style(italic, bold, fontname, mapped_size, mean_size).
    - mapped_font_size: captures most dominant character size within paragraph & maps it to TextSize Enum.
      mapped Size is leveraged by the hierarchy detection algorithm.
    """

    def __init__(self, sizemapper: SizeMapper, style_info: StyleDistribution):
        self._sizeMapper = sizemapper
        self._styleInfo = style_info

    @staticmethod
    def __investigate_box_style(element):
        fonts = Counter()
        sizes = []
        for line in element:
            if isinstance(line, LTChar):
                fonts.update([line.fontname])
                sizes.append(line.size)

            else:
                for c in line:
                    if isinstance(c, LTChar):
                        fonts.update([c.fontname])
                        sizes.append(c.size)
        return fonts, sizes

    def process(self, element_gen):  # element: LTTextContainer):
        """ "
        annotate each element with fontsize
        """
        for element in element_gen:
            if isinstance(element, LTTextBoxHorizontal):
                fonts, sizes = self.__investigate_box_style(element)
                if not fonts or not element.get_text().rstrip():
                    continue

                font_name = fonts.most_common(1)[0][0]
                mean_size = truncate(statistics.mean(sizes), 1)
                max_size = max(sizes)
                # todo currently empty boxes are forwarded.. with holding only \n
                mapped_size = self._sizeMapper.translate(
                    target_enum=TextSize, value=max_size
                )
                s = Style(
                    bold="bold" in str(font_name.lower()),
                    italic="italic" in font_name.lower(),
                    font_name=font_name,
                    mapped_font_size=mapped_size,
                    mean_size=mean_size,
                    max_size=max_size,
                )

                # todo, split lines within LTTextBoxHorizontal
                #  split using style as differentiator
                #  e.g 1st is title with bold text
                #      2nd & 3rd line are introduction lines with body style
                #      -> forward 2 boxes (header, content)
                yield TextElement(
                    text_container=element,
                    style=s,
                    page=element.page if hasattr(element, "page") else None,
                )
