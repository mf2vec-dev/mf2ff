import unittest

from tests.mf2ff_test import Mf2ffTest


class TestLigatureExtension(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_ligature_extension/test_ligature_extension', options={'extension-ligature': True})

    def test_carets(self):
        self.assertEqual(self.font['D'].lcarets, (30, 60))
        self.assertEqual(self.font['E'].lcarets, (30, 40, 70))

    def test_ligatures_by_names(self):
        posSub = self.font['D'].getPosSub('gsub_ligature_liga_subtable')
        self.assertEqual(len(posSub), 1)
        self.assertEqual(posSub[0][1], 'Ligature')
        self.assertEqual(posSub[0][2], 'A')
        self.assertEqual(posSub[0][3], 'B')
        self.assertEqual(posSub[0][4], 'C')

    def test_ligatures_by_code_points(self):
        posSub = self.font['E'].getPosSub('gsub_ligature_liga_subtable')
        self.assertEqual(len(posSub), 1)
        self.assertEqual(posSub[0][1], 'Ligature')
        self.assertEqual(posSub[0][2], 'A')
        self.assertEqual(posSub[0][3], 'B')
        self.assertEqual(posSub[0][4], 'C')
        self.assertEqual(posSub[0][5], 'D')

if __name__ == '__main__':
    unittest.main()
