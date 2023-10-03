import unittest
from math import sqrt

from tests.mf2ff_test import Mf2ffTest


class TestGlyphExtension(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_glyph_extension/test_glyph_extension', debug=True, options={
            'input-encoding': 'TeX-text',
            'extension-glyph': True
        })

    def test_glyph_comment(self):
        glyph = self.font['A']
        self.assertEqual(glyph.comment, 'comment on A')

    def test_glyph_unicode_in_input_encoding(self):
        self.assertIn('Gamma', self.font)

    def test_glyph_unicode_with_name(self):
        self.assertIn('Delta', self.font)

    def test_glyph_unicode_not_in_input_encoding(self):
        self.assertIn('ntilde', self.font)

    def test_glyph_only_name(self):
        self.assertIn('b.sc', self.font)

    def test_glyph_top_accent(self):
        self.assertEqual(self.font['t'].topaccent, 50)

    def test_auto_hint(self):
        glyph = self.font['f']

        self.assertEqual(len(glyph.hhints), 3)
        self.assertEqual(len(glyph.hhints[0]), 2)
        self.assertEqual(glyph.hhints[0][0], 21)
        self.assertEqual(glyph.hhints[0][1], -21)
        self.assertEqual(len(glyph.hhints[1]), 2)
        self.assertEqual(glyph.hhints[1][0], 30)
        self.assertEqual(glyph.hhints[1][1], 10)
        self.assertEqual(len(glyph.hhints[2]), 2)
        self.assertEqual(glyph.hhints[2][0], 60)
        self.assertEqual(glyph.hhints[2][1], 10)

        self.assertEqual(len(glyph.vhints), 1)
        self.assertEqual(len(glyph.vhints[0]), 2)
        self.assertEqual(glyph.vhints[0][0], 10)
        self.assertEqual(glyph.vhints[0][1], 10)

    def test_auto_instruct(self):
        glyph = self.font['f']
        # TODO FontForge doesn't autoInstruct, not even in the GUI
        # NOTE: fontforge.unParseTTInstrs is not the exact reverse of
        # self.fontforge.parseTTInstrs (parseTTInstrs requires str and outputs
        # bytes, unParseTTInstrs requires bytes and outputs bytes)
        self.assertEqual(self.fontforge.unParseTTInstrs(glyph.ttinstrs), b'')

    def test_build(self):
        glyph = self.font['ff']

        self.assertEqual(len(glyph.references), 2)
        self.assertEqual(len(glyph.references[0]), 3)
        self.assertEqual(glyph.references[0][0], 'f')
        self.assertEqual(glyph.references[0][1], (1, 0, 0, 1, 50, 0))
        self.assertEqual(glyph.references[0][2], False)
        self.assertEqual(len(glyph.references[1]), 3)
        self.assertEqual(glyph.references[1][0], 'f')
        self.assertEqual(glyph.references[1][1], (1, 0, 0, 1, 0, 0))
        self.assertEqual(glyph.references[1][2], False)

    def test_add_reference(self):
        glyph = self.font['questiondown']
        self.assertEqual(len(glyph.references), 1)
        self.assertEqual(len(glyph.references[0]), 3)
        self.assertEqual(glyph.references[0][0], 'question')
        self.assertEqual(glyph.references[0][1], (-1, 0, 0, -1, 0, -20))
        self.assertEqual(glyph.references[0][2], False)

    def test_replacement(self):
        gsub_lookup_names = self.font.gsub_lookups
        gsub_lookup_name = 'gsub_single_smcp'
        self.assertIn(gsub_lookup_name, gsub_lookup_names)

        gsub_lookup_info = self.font.getLookupInfo(gsub_lookup_name)
        self.assertEqual(gsub_lookup_info[2][0][0], 'smcp')

        gsub_subtable_names = self.font.getLookupSubtables(gsub_lookup_name)
        gsub_subtable_name = 'gsub_single_smcp_subtable'
        self.assertIn(gsub_subtable_name, gsub_subtable_names)

        b_posSub = self.font['b'].getPosSub(gsub_subtable_name)
        c_posSub = self.font['c'].getPosSub(gsub_subtable_name)
        self.assertEqual(len(b_posSub), 1)
        self.assertEqual(b_posSub[0][1], 'Substitution')
        self.assertEqual(b_posSub[0][2], 'b.sc')
        self.assertEqual(len(c_posSub), 1)
        self.assertEqual(c_posSub[0][1], 'Substitution')
        self.assertEqual(c_posSub[0][2], 'c.sc')

    def test_manual_hints(self):
        glyph = self.font['h']

        hhints = glyph.hhints
        self.assertEqual(len(hhints), 1)
        self.assertEqual(len(hhints[0]), 2)
        self.assertEqual(hhints[0][0], 10)
        self.assertEqual(hhints[0][1], 10)

        vhints = glyph.vhints
        self.assertEqual(len(vhints), 1)
        self.assertEqual(len(vhints[0]), 2)
        self.assertEqual(vhints[0][0], 30)
        self.assertEqual(vhints[0][1], 10)

        dhints = glyph.dhints
        self.assertEqual(len(dhints), 2)
        self.assertEqual(len(dhints[0]), 3)
        self.assertEqual(len(dhints[0][0]), 2)
        self.assertEqual(dhints[0][0][0], 50)
        self.assertEqual(dhints[0][0][1], 60)
        self.assertEqual(len(dhints[0][1]), 2)
        self.assertEqual(dhints[0][1][0], 70)
        self.assertEqual(dhints[0][1][1], 80)
        self.assertEqual(len(dhints[0][2]), 2)
        self.assertAlmostEqual(dhints[0][2][0], sqrt(2)/2)
        self.assertAlmostEqual(dhints[0][2][1], sqrt(2)/2)

if __name__ == '__main__':
    unittest.main()
