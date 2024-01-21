import unittest

from tests.mf2ff_test import Mf2ffTest


class TestExtensible(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_extensible/test_extensible')

    def test_extensible_without_middle(self):
        self.assertEqual(
            self.font["zero"].verticalComponents,
            (
                ('two', 0, 0, 0, 0), # bottom
                ('three', 1, 0, 0, 0), # repeat
                ('one', 0, 0, 0, 0) # top
            )
        )

    def test_extensible_with_middle(self):
        self.assertEqual(
            self.font["A"].verticalComponents,
            (
                ('D', 0, 0, 0, 0), # bottom
                ('E', 1, 0, 0, 0), # repeat
                ('C', 0, 0, 0, 0), # middle
                ('E', 1, 0, 0, 0), # repeat
                ('B', 0, 0, 0, 0) # top
            )
        )

    def test_extensible_from_charlist(self):
        self.assertEqual(
            self.font["a"].verticalComponents,
            (
                ('f', 0, 0, 0, 0), # bottom
                ('g', 1, 0, 0, 0), # repeat
                ('e', 0, 0, 0, 0) # top
            )
        )

if __name__ == '__main__':
    unittest.main()
