import unittest

from tests.mf2ff_test import Mf2ffTest


class TestLigtableGeneralizedCode(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_font_metric_command_generalized_code/test_font_metric_command_generalized_code', debug=True, options={
            'ligtable-generalized-code': True,
            'extension-glyph': True
        })

    def test_kern_with_hex(self):
        subtable_name = 'gpos_pair_subtable'
        a_pos = self.font['a'].getPosSub(subtable_name)
        self.assertEqual(a_pos[2][2], 'Amacron')
        self.assertEqual(a_pos[2][5], -10)

    def test_kern_with_unicode(self):
        subtable_name = 'gpos_pair_subtable'
        a_pos = self.font['a'].getPosSub(subtable_name)
        self.assertEqual(a_pos[0][2], 'uni0200')
        self.assertEqual(a_pos[0][5], -20)

    def test_kern_with_glyph_name(self):
        subtable_name = 'gpos_pair_subtable'
        a_pos = self.font['a'].getPosSub(subtable_name)
        self.assertEqual(a_pos[1][2], 'a.sc')
        self.assertEqual(a_pos[1][5], -30)

    def test_kern_hex_with_unicode(self):
        subtable_name = 'gpos_pair_subtable'
        amacron_sub = self.font['Amacron'].getPosSub(subtable_name)
        self.assertEqual(amacron_sub[0][2], 'uni0200')
        self.assertEqual(amacron_sub[0][5], -40)

    def test_lig_unicode_with_glyph_name_to_hex(self):
        subtable_name = 'gsub_ligature_liga_subtable'
        amacron_sub = self.font['Amacron'].getPosSub(subtable_name)
        self.assertEqual(amacron_sub[0][2], 'uni0200')
        self.assertEqual(amacron_sub[0][3], 'a.sc')

if __name__ == '__main__':
    unittest.main()
