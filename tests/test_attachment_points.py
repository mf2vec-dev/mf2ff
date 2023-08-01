import unittest

from tests.mf2ff_test import Mf2ffTest


class TestAttachmentPoints(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file(
            'test_attachment_points/test_attachment_points',
            False,
            {'extension-attachment-points': True}
        )

    def test_attachment_point_base(self):

        gpos_lookup_names = self.font.gpos_lookups
        gpos_lookup_name_m2b = 'gpos_mark2base'
        self.assertIn(gpos_lookup_name_m2b, gpos_lookup_names)

        gsub_lookup_info = self.font.getLookupInfo(gpos_lookup_name_m2b)
        self.assertEqual(gsub_lookup_info[2][0][0], 'mark')

        gsub_subtable_names = self.font.getLookupSubtables(gpos_lookup_name_m2b)
        gsub_subtable_name = 'gpos_mark2base_subtable'
        self.assertIn(gsub_subtable_name, gsub_subtable_names)


        gpos_lookup_name_m2m = 'gpos_mark2mark'
        self.assertIn(gpos_lookup_name_m2m, gpos_lookup_names)

        gsub_lookup_info = self.font.getLookupInfo(gpos_lookup_name_m2m)
        self.assertEqual(gsub_lookup_info[2][0][0], 'mkmk')

        gsub_subtable_names = self.font.getLookupSubtables(gpos_lookup_name_m2m)
        gsub_subtable_name = 'gpos_mark2mark_subtable'
        self.assertIn(gsub_subtable_name, gsub_subtable_names)


        a_anchorPoints = self.font['A'].anchorPoints
        self.assertEqual(a_anchorPoints[0][0], 'Top')
        self.assertEqual(a_anchorPoints[0][1], 'base')
        self.assertEqual(a_anchorPoints[0][2], 50)
        self.assertEqual(a_anchorPoints[0][3], 100)

        b_anchorPoints = self.font['B'].anchorPoints
        self.assertEqual(b_anchorPoints[0][0], 'TopMark')
        self.assertEqual(b_anchorPoints[0][1], 'basemark')
        self.assertEqual(b_anchorPoints[0][2], 50)
        self.assertEqual(b_anchorPoints[0][3], 100)
        self.assertEqual(b_anchorPoints[1][0], 'Top')
        self.assertEqual(b_anchorPoints[1][1], 'mark')
        self.assertEqual(b_anchorPoints[1][2], 50)
        self.assertEqual(b_anchorPoints[1][3], 50)

        c_anchorPoints = self.font['C'].anchorPoints
        self.assertEqual(c_anchorPoints[0][0], 'TopMark')
        self.assertEqual(c_anchorPoints[0][1], 'mark')
        self.assertEqual(c_anchorPoints[0][2], 50)
        self.assertEqual(c_anchorPoints[0][3], 50)
        self.assertEqual(c_anchorPoints[1][0], 'Top')
        self.assertEqual(c_anchorPoints[1][1], 'mark')
        self.assertEqual(c_anchorPoints[1][2], 50)
        self.assertEqual(c_anchorPoints[1][3], 50)

        # TODO As far as I understand, this is correct. However, the behavior in
        # FontForge's Metrics window is strange for mark2mark.


if __name__ == '__main__':
    unittest.main()

