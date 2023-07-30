import unittest

from tests.mf2ff_test import Mf2ffTest


class TestFilling(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_filling/test_filling')

    def test_empty_glyph(self):
        g = self.font['A']
        bgl = g.layers[0]
        l = g.layers[1]

        self.assertEqual(bgl.isEmpty(), True)
        self.assertEqual(len(bgl), 0)
        self.assertEqual(l.isEmpty(), True)
        self.assertEqual(len(l), 0)

    def test_contour_and_points(self):
        g = self.font['B']
        bgl = g.layers[0]
        l = g.layers[1]

        self.assertEqual(bgl.isEmpty(), True)
        self.assertEqual(len(bgl), 0)
        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]

        # 3 defined points; every point is proceeded by two control points
        self.assertEqual(len(c), 3*3)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertEqual(c[0].x, 1)
        self.assertEqual(c[0].y, 2)
        self.assertEqual(c[0].on_curve, True)
        self.assertAlmostEqual(c[1].x, c[0].x + 1/3*(c[3].x - c[0].x), places=4)
        self.assertAlmostEqual(c[1].y, c[0].y + 1/3*(c[3].y - c[0].y), places=4)
        self.assertEqual(c[1].on_curve, False)
        self.assertAlmostEqual(c[2].x, c[0].x + 2/3*(c[3].x - c[0].x), places=4)
        self.assertAlmostEqual(c[2].y, c[0].y + 2/3*(c[3].y - c[0].y), places=4)
        self.assertEqual(c[2].on_curve, False)
        self.assertEqual(c[3].x, 3)
        self.assertEqual(c[3].y, 4)
        self.assertEqual(c[3].on_curve, True )
        self.assertAlmostEqual(c[4].x, c[3].x + 1/3*(c[6].x - c[3].x), places=4)
        self.assertAlmostEqual(c[4].y, c[3].y + 1/3*(c[6].y - c[3].y), places=4)
        self.assertEqual(c[4].on_curve, False)
        self.assertAlmostEqual(c[5].x, c[3].x + 2/3*(c[6].x - c[3].x), places=4)
        self.assertAlmostEqual(c[5].y, c[3].y + 2/3*(c[6].y - c[3].y), places=4)
        self.assertEqual(c[5].on_curve, False)
        self.assertEqual(c[6].x, 6)
        self.assertEqual(c[6].y, 5)
        self.assertEqual(c[6].on_curve, True)
        self.assertAlmostEqual(c[7].x, c[6].x + 1/3*(c[0].x - c[6].x), places=4)
        self.assertAlmostEqual(c[7].y, c[6].y + 1/3*(c[0].y - c[6].y), places=4)
        self.assertEqual(c[7].on_curve, False)
        self.assertAlmostEqual(c[8].x, c[6].x + 2/3*(c[0].x - c[6].x), places=4)
        self.assertAlmostEqual(c[8].y, c[6].y + 2/3*(c[0].y - c[6].y), places=4)
        self.assertEqual(c[8].on_curve, False)

    def test_clockwise(self):
        # checks if a clockwise path in METAFONT is added clockwise
        g = self.font['C']
        l = g.layers[1]
        c = l[0]
        self.assertEqual(c.isClockwise(), True)

    def test_counter_clockwise(self):
        # checks if a counter-clockwise path in METAFONT is added clockwise
        g = self.font['D']
        l = g.layers[1]
        c = l[0]
        self.assertEqual(c.isClockwise(), True)

    def test_outer_and_inner(self):
        # checks if negative withweight results in counter-clockwise path for inner contour
        g = self.font['E']
        l = g.layers[1]
        c0 = l[0]
        c1 = l[1]
        self.assertEqual(c0.isClockwise(), True)
        self.assertEqual(c1.isClockwise(), False)

if __name__ == '__main__':
    unittest.main()
