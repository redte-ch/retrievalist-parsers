from pathlib import Path
from unittest import TestCase

from retrievalist_parsers import utils


class Test(TestCase):
    test_path_1 = str(Path("tests/resources/interview_cheatsheet.pdf").absolute())

    def test_word_generator(self):
        elements = utils.generate_text_elements(self.test_path_1)

        # 1st text container
        element = next(elements)
        words = list(utils.generate_words(element))
        self.assertEqual(1, len(words))
        self.assertEqual("31/10/2019", " ".join(words))

        # 2nd text container
        element = next(elements)
        words = list(utils.generate_words(element))
        self.assertEqual(31, len(words))
        self.assertEqual(
            "This is my technical interview cheat sheet.", " ".join(words[:7])
        )
