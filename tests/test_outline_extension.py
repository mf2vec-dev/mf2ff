import unittest
from math import sqrt

from tests.mf2ff_test import Mf2ffTest


class TestOutlineExtension(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_outline_extension/test_outline_extension', options={'extension-outline': True, 'debug': True})

    def test_sort_canonical(self):
        self.assertEqual(self.font['A'].foreground[0][0].x, -0.5)
        self.assertEqual(self.font['A'].foreground[0][0].y, 0)
        self.assertEqual(self.font['A'].foreground[1][0].x, -0.5)
        self.assertEqual(self.font['A'].foreground[1][0].y, 10)
        self.assertEqual(self.font['A'].foreground[2][0].x, 9.5)
        self.assertEqual(self.font['A'].foreground[2][0].y, 10)

    def test_sort_dir(self):
        self.assertAlmostEqual(self.font['B'].foreground[0][0].x, -sqrt(1/2)/2, places=3)
        self.assertAlmostEqual(self.font['B'].foreground[0][0].y, 10+sqrt(1/2)/2, places=3)
        self.assertAlmostEqual(self.font['B'].foreground[1][0].x, -sqrt(1/2)/2, places=3)
        self.assertAlmostEqual(self.font['B'].foreground[1][0].y, sqrt(1/2)/2, places=3)
        self.assertAlmostEqual(self.font['B'].foreground[2][0].x, 10-sqrt(1/2)/2, places=3)
        self.assertAlmostEqual(self.font['B'].foreground[2][0].y, 10+sqrt(1/2)/2, places=3)

    def test_point_name_by_coords_and_set_first_point(self):
        self.assertAlmostEqual(self.font['C'].foreground[0][0].x, sqrt(1/2)/2, places=3)
        self.assertAlmostEqual(self.font['C'].foreground[0][0].y, sqrt(1/2)/2, places=3)

    def test_point_name_by_index_and_set_first_point(self):
        self.assertAlmostEqual(self.font['D'].foreground[1][0].x, 10*sqrt(1/2)/2, places=3)
        self.assertAlmostEqual(self.font['D'].foreground[1][0].y, 10*sqrt(1/2)/2, places=3)

    def test_point_name_by_index_and_set_first_contour(self):
        self.assertEqual(self.font['E'].foreground[0][0].x, 5)
        self.assertEqual(self.font['E'].foreground[0][0].y, 0)

    def test_point_name_by_index_and_delete(self):
        self.assertEqual(len(self.font['F'].foreground[0]), 21)
        self.assertAlmostEqual(self.font['F'].foreground[0][19].x, 0.276, places=3)
        self.assertEqual(self.font['F'].foreground[0][19].y, 0.5)
        self.assertEqual(self.font['F'].foreground[0][20].x, 0.5)
        self.assertAlmostEqual(self.font['F'].foreground[0][20].y, 0.276, places=3)

    def test_point_name_by_index_and_delete_contour(self):
        self.assertEqual(len(self.font['G'].foreground), 1)

if __name__ == '__main__':
    unittest.main()
