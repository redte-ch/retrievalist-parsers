import itertools
from collections import Counter
from pathlib import Path
from unittest import TestCase

import pandas as pd

from retrievalist_parsers import utils
from retrievalist_parsers.analysis.annotate import StyleAnnotator
from retrievalist_parsers.analysis.sizemapper import PivotLinearMapper, PivotLogMapper
from retrievalist_parsers.analysis.styledistribution import (
    StyleDistribution,
    count_sizes,
)
from retrievalist_parsers.model.style import TextSize
from retrievalist_parsers.utils import DocumentTypeFilter


class TestSizeMapper(TestCase):
    def test_log_mapper(self):
        distribution = StyleDistribution(Counter((1, 5, 6, 10, 10, 10, 10, 20, 100)))
        scaler = PivotLogMapper(distribution)
        # test borders
        borders = (4.02, 8.01, 14.41, 23.28)
        [self.assertAlmostEqual(borders[i], b, 1) for i, b in enumerate(scaler.borders)]
        self.assertEqual(TextSize.xsmall, scaler.translate(TextSize, -10))
        self.assertEqual(TextSize.xsmall, scaler.translate(TextSize, 0))
        self.assertEqual(TextSize.xsmall, scaler.translate(TextSize, 1))
        self.assertEqual(TextSize.small, scaler.translate(TextSize, 5))
        self.assertEqual(TextSize.small, scaler.translate(TextSize, 6))
        self.assertEqual(TextSize.small, scaler.translate(TextSize, 7))
        self.assertEqual(TextSize.small, scaler.translate(TextSize, 8))
        self.assertEqual(TextSize.middle, scaler.translate(TextSize, 10))
        self.assertEqual(TextSize.middle, scaler.translate(TextSize, 12))
        self.assertEqual(TextSize.large, scaler.translate(TextSize, 15))
        self.assertEqual(TextSize.large, scaler.translate(TextSize, 16))
        self.assertEqual(TextSize.large, scaler.translate(TextSize, 20))
        self.assertEqual(TextSize.xlarge, scaler.translate(TextSize, 30))
        self.assertEqual(TextSize.xlarge, scaler.translate(TextSize, 200))

    def test_linear_mapper(self):
        distribution = StyleDistribution(Counter((1, 5, 6, 10, 10, 10, 10, 20, 100)))
        scaler = PivotLinearMapper(distribution)

        self.assertTupleEqual((3.25, 5.5, 32.5, 55.0), scaler.borders)

        self.assertEqual(TextSize.xsmall, scaler.translate(TextSize, -10))
        self.assertEqual(TextSize.xsmall, scaler.translate(TextSize, 0))
        self.assertEqual(TextSize.xsmall, scaler.translate(TextSize, 1))
        self.assertEqual(TextSize.small, scaler.translate(TextSize, 5))
        self.assertEqual(TextSize.middle, scaler.translate(TextSize, 10))
        self.assertEqual(TextSize.middle, scaler.translate(TextSize, 15))
        self.assertEqual(TextSize.middle, scaler.translate(TextSize, 20))
        self.assertEqual(TextSize.middle, scaler.translate(TextSize, 30))
        self.assertEqual(TextSize.large, scaler.translate(TextSize, 40))
        self.assertEqual(TextSize.large, scaler.translate(TextSize, 50))
        self.assertEqual(TextSize.xlarge, scaler.translate(TextSize, 60))
        self.assertEqual(TextSize.xlarge, scaler.translate(TextSize, 70))
        self.assertEqual(TextSize.xlarge, scaler.translate(TextSize, 90))
        self.assertEqual(TextSize.xlarge, scaler.translate(TextSize, 120))


class TestFonts(TestCase):
    def test_fontnames(self):
        fonts = []
        for file in itertools.islice(
            utils.find_file(
                str(Path("tests/resources/").absolute()),
                DocumentTypeFilter(endings=("pdf")),
            ),
            3,
        ):
            if not file.is_file():
                continue
            file_path = str(file.absolute())
            distribution = count_sizes(utils.generate_text_elements(file_path))

            sizeMapper = PivotLogMapper(distribution)
            style_annotator = StyleAnnotator(
                sizemapper=sizeMapper, style_info=distribution
            )

            elements = utils.generate_text_elements(file_path)
            with_style = style_annotator.process(elements)

            for data in with_style:
                fonts.append(data.style.font_name)

        ds = pd.Series(fonts, name="fonts", dtype=str)
        boldmasked = ds.loc[ds.apply(lambda x: "bold" in x.lower())]
        italic = ds.loc[ds.apply(lambda x: "italic" in x.lower())]

        # todo, define test scenario for sample files
