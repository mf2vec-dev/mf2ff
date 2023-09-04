import unittest

from tests.mf2ff_test import Mf2ffTest


class TestLigtable(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_ligtable/test_ligtable')

    def test_kerning(self):
        # test the 'kern' subcommand

        gpos_lookup_names = self.font.gpos_lookups
        gpos_lookup_name = gpos_lookup_names[0]
        gpos_lookup_info = self.font.getLookupInfo(gpos_lookup_name)

        self.assertEqual(gpos_lookup_info[2][0][0], 'kern')
        # TODO gpos_lookup_info has many other values!

        gpos_subtable_names = self.font.getLookupSubtables(gpos_lookup_name)
        gpos_subtable_name = gpos_subtable_names[0]
        a_posSub = self.font['A'].getPosSub(gpos_subtable_name)

        self.assertEqual(len(a_posSub), 1)
        self.assertEqual(a_posSub[0][1], 'Pair')
        self.assertEqual(a_posSub[0][2], 'B')
        self.assertEqual(a_posSub[0][3], 0)
        self.assertEqual(a_posSub[0][4], 0)
        self.assertEqual(a_posSub[0][5], 10)
        self.assertEqual(a_posSub[0][6], 0)
        self.assertEqual(a_posSub[0][7], 0)
        self.assertEqual(a_posSub[0][8], 0)
        self.assertEqual(a_posSub[0][9], 0)
        self.assertEqual(a_posSub[0][10], 0)

    def test_ligature_ec(self):
        # test the '=:' (equal-colon) subcommand and multiple commands

        gsub_lookup_names = self.font.gsub_lookups
        gsub_lookup_name = 'gsub_ligature_liga'
        self.assertIn(gsub_lookup_name, gsub_lookup_names)

        gsub_lookup_info = self.font.getLookupInfo(gsub_lookup_name)
        self.assertEqual(gsub_lookup_info[2][0][0], 'liga')
        # gpos_lookup_info has many other values!

        gsub_subtable_names = self.font.getLookupSubtables(gsub_lookup_name)
        gsub_subtable_name = 'gsub_ligature_liga_subtable'
        self.assertIn(gsub_subtable_name, gsub_subtable_names)

        e_posSub = self.font['E'].getPosSub(gsub_subtable_name)
        g_posSub = self.font['G'].getPosSub(gsub_subtable_name)
        self.assertEqual(len(e_posSub), 1)
        self.assertEqual(e_posSub[0][1], 'Ligature')
        self.assertEqual(e_posSub[0][2], 'C')
        self.assertEqual(e_posSub[0][3], 'D')
        self.assertEqual(len(g_posSub), 1)
        self.assertEqual(g_posSub[0][1], 'Ligature')
        self.assertEqual(g_posSub[0][2], 'C')
        self.assertEqual(g_posSub[0][3], 'F')

    def test_ligature_pec(self):
        # test the '|=:' (equal-colon-pipe) subcommand and multiple commands

        gsub_lookup_names = self.font.gsub_lookups
        gsub_lookup_name = 'gsub_contextchain'
        self.assertIn(gsub_lookup_name, gsub_lookup_names)

        gsub_lookup_info = self.font.getLookupInfo(gsub_lookup_name)
        self.assertEqual(gsub_lookup_info[2][0][0], 'calt')
        # gpos_lookup_info has many other values!

        gsub_subtable_names = self.font.getLookupSubtables(gsub_lookup_name)
        gsub_subtable_name = 'gsub_contextchain_subtable_H_I'
        self.assertIn(gsub_subtable_name, gsub_subtable_names)

        # TODO how to check rule of subtable?


        gsub_lookup_name = 'gsub_single_after_H'
        self.assertIn(gsub_lookup_name, gsub_lookup_names)

        gsub_lookup_info = self.font.getLookupInfo(gsub_lookup_name)
        self.assertEqual(gsub_lookup_info[0], 'gsub_single')

        gsub_subtable_names = self.font.getLookupSubtables(gsub_lookup_name)
        gsub_subtable_name = 'gsub_single_after_H_subtable'
        self.assertIn(gsub_subtable_name, gsub_subtable_names)

        i_subPos = self.font['I'].getPosSub(gsub_subtable_name)
        self.assertEqual(i_subPos[0][1], 'Substitution')
        self.assertEqual(i_subPos[0][2], 'J')

    def test_ligature_ecp(self):
        # test the '=:|' (equal-colon-pipe) subcommand and multiple commands

        gsub_lookup_names = self.font.gsub_lookups
        gsub_lookup_name = 'gsub_contextchain'
        self.assertIn(gsub_lookup_name, gsub_lookup_names)

        gsub_lookup_info = self.font.getLookupInfo(gsub_lookup_name)
        self.assertEqual(gsub_lookup_info[2][0][0], 'calt')
        # gpos_lookup_info has many other values!

        gsub_subtable_names = self.font.getLookupSubtables(gsub_lookup_name)
        gsub_subtable_name = 'gsub_contextchain_subtable_K_L'

        self.assertIn(gsub_subtable_name, gsub_subtable_names)

        # TODO how to check rule of subtable?


        gsub_lookup_name = 'gsub_single_before_L'
        self.assertIn(gsub_lookup_name, gsub_lookup_names)

        gsub_lookup_info = self.font.getLookupInfo(gsub_lookup_name)
        self.assertEqual(gsub_lookup_info[0], 'gsub_single')

        gsub_subtable_names = self.font.getLookupSubtables(gsub_lookup_name)
        gsub_subtable_name = 'gsub_single_before_L_subtable'
        self.assertIn(gsub_subtable_name, gsub_subtable_names)

        i_subPos = self.font['K'].getPosSub(gsub_subtable_name)
        self.assertEqual(i_subPos[0][1], 'Substitution')
        self.assertEqual(i_subPos[0][2], 'M')

    def test_kerning_before_chars(self):
        # test the 'kern' subcommand before definition of chars

        gpos_lookup_names = self.font.gpos_lookups
        gpos_lookup_name = gpos_lookup_names[0]
        gpos_subtable_names = self.font.getLookupSubtables(gpos_lookup_name)
        gpos_subtable_name = gpos_subtable_names[0]
        n_posSub = self.font['N'].getPosSub(gpos_subtable_name)

        self.assertEqual(len(n_posSub), 1)
        self.assertEqual(n_posSub[0][1], 'Pair')
        self.assertEqual(n_posSub[0][2], 'O')
        self.assertEqual(n_posSub[0][3], 0)
        self.assertEqual(n_posSub[0][4], 0)
        self.assertEqual(n_posSub[0][5], -20)
        self.assertEqual(n_posSub[0][6], 0)
        self.assertEqual(n_posSub[0][7], 0)
        self.assertEqual(n_posSub[0][8], 0)
        self.assertEqual(n_posSub[0][9], 0)
        self.assertEqual(n_posSub[0][10], 0)

    def test_ligature_ec_before_chars(self):
        # test the '=:' (equal-colon) subcommand before definition of chars

        gsub_subtable_name = 'gsub_ligature_liga_subtable'
        r_posSub = self.font['R'].getPosSub(gsub_subtable_name)
        self.assertEqual(len(r_posSub), 1)
        self.assertEqual(r_posSub[0][1], 'Ligature')
        self.assertEqual(r_posSub[0][2], 'P')
        self.assertEqual(r_posSub[0][3], 'Q')

if __name__ == '__main__':
    unittest.main()
