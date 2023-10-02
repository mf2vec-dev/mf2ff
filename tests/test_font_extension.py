import unittest

from tests.mf2ff_test import Mf2ffTest


class TestFontExtension(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_font_extension/test_font_extension', debug=True, options={
            'extension-font': True
        })

    def test_name(self):
        self.assertEqual(self.font.fontname, 'test-font')

    def test_ascent(self):
        self.assertEqual(self.font.ascent, 8)

    def test_math(self):
        self.assertEqual(self.font.math.ScriptPercentScaleDown, 70)

    def test_ps_private(self):
        self.assertEqual(self.font.private['BlueValues'], (-10, 0, 100, 110))

if __name__ == '__main__':
    unittest.main()
