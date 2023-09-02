import unittest

from tests.mf2ff_test import Mf2ffTest


class TestLigtableSwitch(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_ligtable_switch/test_ligtable_switch', debug=True, options={'extension-ligtable-switch': True})

    def test_lookups(self):
        gsub_lookup_names = self.font.gsub_lookups

        for ot_feature in ['liga', 'dlig', 'hlig']:
            gsub_lookup_name = 'gsub_ligature_' + ot_feature
            self.assertIn(gsub_lookup_name, gsub_lookup_names)

            gsub_lookup_info = self.font.getLookupInfo(gsub_lookup_name)
            self.assertEqual(gsub_lookup_info[2][0][0], ot_feature)

            gsub_subtable_names = self.font.getLookupSubtables(gsub_lookup_name)
            gsub_subtable_name = 'gsub_ligature_' + ot_feature + '_subtable'
            self.assertIn(gsub_subtable_name, gsub_subtable_names)

    def test_ligatures(self):
        for lig, a, b, gsub_subtable_name in [
            ('C', 'A', 'B', 'gsub_ligature_liga_subtable'),
            ('F', 'D', 'E', 'gsub_ligature_liga_subtable'),
            ('H', 'D', 'G', 'gsub_ligature_liga_subtable'),
            ('c', 'a', 'b', 'gsub_ligature_dlig_subtable'),
            ('f', 'd', 'e', 'gsub_ligature_dlig_subtable'),
            ('h', 'd', 'g', 'gsub_ligature_dlig_subtable'),
            ('P', 'N', 'O', 'gsub_ligature_hlig_subtable'),
            ('S', 'Q', 'R', 'gsub_ligature_hlig_subtable'),
            ('U', 'Q', 'T', 'gsub_ligature_hlig_subtable'),
            ('p', 'n', 'o', 'gsub_ligature_liga_subtable'),
            ('s', 'q', 'r', 'gsub_ligature_liga_subtable'),
            ('u', 'q', 't', 'gsub_ligature_liga_subtable'),
        ]:
            posSub = self.font[lig].getPosSub(gsub_subtable_name)
            self.assertEqual(len(posSub), 1)
            self.assertEqual(posSub[0][1], 'Ligature')
            self.assertEqual(posSub[0][2], a)
            self.assertEqual(posSub[0][3], b)

if __name__ == '__main__':
    unittest.main()
