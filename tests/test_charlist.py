import unittest

from tests.mf2ff_test import Mf2ffTest


class TestCharlist(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_charlist/test_charlist')

    def test_extensible(self):
        self.assertEqual(self.font["zero"].verticalVariants, "one two three")

if __name__ == '__main__':
    unittest.main()
