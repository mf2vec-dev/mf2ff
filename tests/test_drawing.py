import unittest

from tests.mf2ff_test import Mf2ffTest


class TestDrawing(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_drawing/test_drawing', debug=True)

    def test_dot_convex(self):
        g = self.font['A']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 3)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertEqual(P[0].x, 5)
        self.assertEqual(P[0].y, 10)
        self.assertEqual(P[1].x, 10)
        self.assertEqual(P[1].y, 20)
        self.assertEqual(P[2].x, 15)
        self.assertEqual(P[2].y, 10)

    def test_line_convex(self):
        g = self.font['B']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 4)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertEqual(P[0].x, 65)
        self.assertEqual(P[0].y, 20)
        self.assertEqual(P[1].x, 15)
        self.assertEqual(P[1].y, 20)
        self.assertEqual(P[2].x, 20)
        self.assertEqual(P[2].y, 30)
        self.assertEqual(P[3].x, 60)
        self.assertEqual(P[3].y, 30)

    def test_line_elliptical(self):
        g = self.font['C']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        P = [p for p in c if p.on_curve]
        self.assertEqual(len(P), 6)
        self.assertEqual(P[0].x, 20)
        self.assertEqual(P[0].y, 15)
        self.assertEqual(P[1].x, 15)
        self.assertEqual(P[1].y, 20)
        self.assertEqual(P[2].x, 20)
        self.assertEqual(P[2].y, 25)
        self.assertEqual(P[3].x, 60)
        self.assertEqual(P[3].y, 25)
        self.assertEqual(P[4].x, 65)
        self.assertEqual(P[4].y, 20)
        self.assertEqual(P[5].x, 60)
        self.assertEqual(P[5].y, 15)

        P = [p for p in c if not p.on_curve]
        self.assertEqual(len(P), 8)
        self.assertAlmostEqual(P[0].x, 17.240, places=1)
        self.assertEqual(P[0].y, 15)
        self.assertEqual(P[1].x, 15)
        self.assertAlmostEqual(P[1].y, 17.240, places=1)
        self.assertEqual(P[2].x, 15)
        self.assertAlmostEqual(P[2].y, 22.759, places=1)
        self.assertAlmostEqual(P[3].x, 17.240, places=1)
        self.assertEqual(P[3].y, 25)
        self.assertAlmostEqual(P[4].x, 62.760, places=1)
        self.assertEqual(P[4].y, 25)
        self.assertEqual(P[5].x, 65)
        self.assertAlmostEqual(P[5].y, 22.760, places=1)
        self.assertEqual(P[6].x, 65)
        self.assertAlmostEqual(P[6].y, 17.240, places=1)
        self.assertAlmostEqual(P[7].x, 62.760, places=1)
        self.assertEqual(P[7].y, 15)


    def test_open_convex(self):
        g = self.font['D']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 10)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertEqual(P[0].x, 15)
        self.assertEqual(P[0].y, 10)
        self.assertEqual(P[1].x, 5)
        self.assertEqual(P[1].y, 10)
        self.assertEqual(P[2].x, 10)
        self.assertEqual(P[2].y, 20)
        self.assertAlmostEqual(P[3].x, 80.588, places=1)
        self.assertAlmostEqual(P[3].y, 28.824, places=1)
        self.assertAlmostEqual(P[4].x, 58.333, places=1)
        self.assertAlmostEqual(P[4].y, 73.333, places=1)
        self.assertEqual(P[5].x, 15)
        self.assertEqual(P[5].y, 30)
        self.assertEqual(P[6].x, 5)
        self.assertEqual(P[6].y, 30)
        self.assertEqual(P[7].x, 10)
        self.assertEqual(P[7].y, 40)
        self.assertEqual(P[8].x, 60)
        self.assertEqual(P[8].y, 90)
        self.assertEqual(P[9].x, 95)
        self.assertEqual(P[9].y, 20)

    def test_overlap_convex(self):
        g = self.font['E']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 2)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 7)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertEqual(P[0].x, 15)
        self.assertEqual(P[0].y, 10)
        self.assertEqual(P[1].x, 5)
        self.assertEqual(P[1].y, 10)
        self.assertEqual(P[2].x, 7.5)
        self.assertEqual(P[2].y, 15)
        self.assertEqual(P[3].x, 5)
        self.assertEqual(P[3].y, 15)
        self.assertEqual(P[4].x, 10)
        self.assertEqual(P[4].y, 25)
        self.assertEqual(P[5].x, 60)
        self.assertEqual(P[5].y, 90)
        self.assertEqual(P[6].x, 95)
        self.assertEqual(P[6].y, 20)

        c = l[1]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 3)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), False)

        self.assertAlmostEqual(P[0].x, 80.588, places=1)
        self.assertAlmostEqual(P[0].y, 28.824, places=1)
        self.assertAlmostEqual(P[1].x, 58.939, places=1)
        self.assertAlmostEqual(P[1].y, 72.121, places=1)
        self.assertAlmostEqual(P[2].x, 19.787, places=1)
        self.assertAlmostEqual(P[2].y, 21.223, places=1)

    def test_closed_convex(self):
        g = self.font['F']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 2)

        if len(l[0]) > len(l[1]):
            cOuter, cInner = l
        else:
            cInner, cOuter = l

        # outer
        P = [p for p in cOuter if p.on_curve]

        self.assertEqual(len(P), 5)
        self.assertEqual(cOuter.closed, True)
        self.assertEqual(cOuter.isClockwise(), True)

        self.assertEqual(P[0].x, 15)
        self.assertEqual(P[0].y, 10)
        self.assertEqual(P[1].x, 5)
        self.assertEqual(P[1].y, 10)
        self.assertEqual(P[2].x, 10)
        self.assertEqual(P[2].y, 20)
        self.assertEqual(P[3].x, 60)
        self.assertEqual(P[3].y, 90)
        self.assertEqual(P[4].x, 95)
        self.assertEqual(P[4].y, 20)

        # inner
        P = [p for p in cInner if p.on_curve]

        self.assertEqual(len(P), 3)
        self.assertEqual(cInner.closed, True)
        self.assertEqual(cInner.isClockwise(), False)

        self.assertAlmostEqual(P[0].x, 59.118, places=1)
        self.assertAlmostEqual(P[0].y, 71.765, places=1)
        self.assertAlmostEqual(P[1].x, 23.333, places=1)
        self.assertAlmostEqual(P[1].y, 21.667, places=1)
        self.assertAlmostEqual(P[2].x, 80.588, places=1)
        self.assertAlmostEqual(P[2].y, 28.824, places=1)

    def test_closed_elliptical(self):
        g = self.font['G']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 2)

        c = l[1]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 4)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertAlmostEqual(P[0].x, 40.892, places=1)
        self.assertAlmostEqual(P[0].y, 53.917, places=1)
        self.assertAlmostEqual(P[1].x, 54.871, places=1)
        self.assertAlmostEqual(P[1].y, 40.721, places=1)
        self.assertAlmostEqual(P[2].x, 39.108, places=1)
        self.assertAlmostEqual(P[2].y, 26.083, places=1)
        self.assertAlmostEqual(P[3].x, 25.129, places=1)
        self.assertAlmostEqual(P[3].y, 39.279, places=1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 4)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), False)

        self.assertAlmostEqual(P[0].x, 40.892, places=1)
        self.assertAlmostEqual(P[0].y, 33.917, places=1)
        self.assertAlmostEqual(P[1].x, 45.129, places=1)
        self.assertAlmostEqual(P[1].y, 39.279, places=1)
        self.assertAlmostEqual(P[2].x, 39.108, places=1)
        self.assertAlmostEqual(P[2].y, 46.083, places=1)
        self.assertAlmostEqual(P[3].x, 34.871, places=1)
        self.assertAlmostEqual(P[3].y, 40.721, places=1)

    def test_contour_pen(self):
        g = self.font['H']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 8)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertEqual(P[0].x, 5)
        self.assertEqual(P[0].y, 10)
        self.assertEqual(P[1].x, 5)
        self.assertEqual(P[1].y, 20)
        self.assertEqual(P[2].x, 10)
        self.assertEqual(P[2].y, 25)
        self.assertEqual(P[3].x, 20)
        self.assertEqual(P[3].y, 25)
        self.assertEqual(P[4].x, 25)
        self.assertEqual(P[4].y, 20)
        self.assertEqual(P[5].x, 25)
        self.assertEqual(P[5].y, 10)
        self.assertEqual(P[6].x, 20)
        self.assertEqual(P[6].y, 5)
        self.assertEqual(P[7].x, 10)
        self.assertEqual(P[7].y, 5)

if __name__ == '__main__':
    unittest.main()