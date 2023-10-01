import unittest
from math import sqrt

from tests.mf2ff_test import Mf2ffTest


class TestAsciiHex(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_ascii_hex/test_ascii_hex', debug=True, options={
            'input-encoding': 'TeX-text',
            'charcode-from-last-ASCII-hex-arg': True
        })

    def test_glyph_unicode_in_input_encoding(self):
        self.assertIn('Gamma', self.font)

    def test_glyph_unicode_with_name(self):
        self.assertIn('Pi', self.font)

if __name__ == '__main__':
    unittest.main()
