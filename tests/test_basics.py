import unittest

from tests.mf2ff_test import Mf2ffTest


class TestBasics(Mf2ffTest):
    def test_character_code_and_dimensions(self):
        # tests 
        self.run_mf_file('test_basics/test_basics_1')

        glyph = self.font['A']

        self.assertEqual(glyph.width, 1)
        self.assertEqual(glyph.texheight, 2)
        self.assertEqual(glyph.texdepth, 3)
        self.assertEqual(self.font.ascent, 2)
        self.assertEqual(self.font.descent, 3)

    def test_increasing_dimensions(self):
        # tests if glyphs with increasing dimensions causes font to take largest
        # dimensions
        self.run_mf_file('test_basics/test_basics_2')

        self.assertEqual(self.font.ascent, 3)
        self.assertEqual(self.font.descent, 3)

    def test_decreasing_dimensions(self):
        # tests if glyphs with decreasing dimensions causes font to take largest
        # dimensions
        self.run_mf_file('test_basics/test_basics_3')

        self.assertEqual(self.font.ascent, 3)
        self.assertEqual(self.font.descent, 3)

if __name__ == '__main__':
    unittest.main()