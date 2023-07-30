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

        self.assertEqual(P[0].x, 50)
        self.assertEqual(P[0].y, 100)
        self.assertEqual(P[1].x, 100)
        self.assertEqual(P[1].y, 200)
        self.assertEqual(P[2].x, 150)
        self.assertEqual(P[2].y, 100)

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

        self.assertEqual(P[0].x, 650)
        self.assertEqual(P[0].y, 200)
        self.assertEqual(P[1].x, 150)
        self.assertEqual(P[1].y, 200)
        self.assertEqual(P[2].x, 200)
        self.assertEqual(P[2].y, 300)
        self.assertEqual(P[3].x, 600)
        self.assertEqual(P[3].y, 300)

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
        self.assertEqual(P[0].x, 200)
        self.assertEqual(P[0].y, 150)
        self.assertEqual(P[1].x, 150)
        self.assertEqual(P[1].y, 200)
        self.assertEqual(P[2].x, 200)
        self.assertEqual(P[2].y, 250)
        self.assertEqual(P[3].x, 600)
        self.assertEqual(P[3].y, 250)
        self.assertEqual(P[4].x, 650)
        self.assertEqual(P[4].y, 200)
        self.assertEqual(P[5].x, 600)
        self.assertEqual(P[5].y, 150)

        P = [p for p in c if not p.on_curve]
        self.assertEqual(len(P), 8)
        self.assertAlmostEqual(P[0].x, 172.40, places=1)
        self.assertEqual(P[0].y, 150)
        self.assertEqual(P[1].x, 150)
        self.assertAlmostEqual(P[1].y, 172.40, places=1)
        self.assertEqual(P[2].x, 150)
        self.assertAlmostEqual(P[2].y, 227.59, places=1)
        self.assertAlmostEqual(P[3].x, 172.40, places=1)
        self.assertEqual(P[3].y, 250)
        self.assertAlmostEqual(P[4].x, 627.60, places=1)
        self.assertEqual(P[4].y, 250)
        self.assertEqual(P[5].x, 650)
        self.assertAlmostEqual(P[5].y, 227.60, places=1)
        self.assertEqual(P[6].x, 650)
        self.assertAlmostEqual(P[6].y, 172.40, places=1)
        self.assertAlmostEqual(P[7].x, 627.60, places=1)
        self.assertEqual(P[7].y, 150)


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

        self.assertEqual(P[0].x, 350)
        self.assertEqual(P[0].y, 300)
        self.assertEqual(P[1].x, 250)
        self.assertEqual(P[1].y, 300)
        self.assertEqual(P[2].x, 300)
        self.assertEqual(P[2].y, 400)
        self.assertAlmostEqual(P[3].x, 556.67, places=1)
        self.assertAlmostEqual(P[3].y, 436.67, places=1)
        self.assertAlmostEqual(P[4].x, 477.27, places=1)
        self.assertAlmostEqual(P[4].y, 595.45, places=1)
        self.assertEqual(P[5].x, 350)
        self.assertEqual(P[5].y, 500)
        self.assertEqual(P[6].x, 250)
        self.assertEqual(P[6].y, 500)
        self.assertEqual(P[7].x, 300)
        self.assertEqual(P[7].y, 600)
        self.assertEqual(P[8].x, 500)
        self.assertEqual(P[8].y, 750)
        self.assertEqual(P[9].x, 700)
        self.assertEqual(P[9].y, 350)

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

        self.assertEqual(P[0].x, 350)
        self.assertEqual(P[0].y, 300)
        self.assertEqual(P[1].x, 250)
        self.assertEqual(P[1].y, 300)
        self.assertEqual(P[2].x, 275)
        self.assertEqual(P[2].y, 350)
        self.assertEqual(P[3].x, 250)
        self.assertEqual(P[3].y, 350)
        self.assertEqual(P[4].x, 300)
        self.assertEqual(P[4].y, 450)
        self.assertEqual(P[5].x, 500)
        self.assertEqual(P[5].y, 750)
        self.assertEqual(P[6].x, 700)
        self.assertEqual(P[6].y, 350)

        c = l[1]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 3)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), False)

        self.assertAlmostEqual(P[0].x, 556.67, places=1)
        self.assertAlmostEqual(P[0].y, 436.67, places=1)
        self.assertAlmostEqual(P[1].x, 492.86, places=1)
        self.assertAlmostEqual(P[1].y, 564.29, places=1)
        self.assertAlmostEqual(P[2].x, 392.11, places=1)
        self.assertAlmostEqual(P[2].y, 413.16, places=1)

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

        self.assertEqual(P[0].x, 350)
        self.assertEqual(P[0].y, 300)
        self.assertEqual(P[1].x, 250)
        self.assertEqual(P[1].y, 300)
        self.assertEqual(P[2].x, 300)
        self.assertEqual(P[2].y, 400)
        self.assertEqual(P[3].x, 500)
        self.assertEqual(P[3].y, 750)
        self.assertEqual(P[4].x, 700)
        self.assertEqual(P[4].y, 350)

        # inner
        P = [p for p in cInner if p.on_curve]

        self.assertEqual(len(P), 3)
        self.assertEqual(cInner.closed, True)
        self.assertEqual(cInner.isClockwise(), False)

        self.assertAlmostEqual(P[0].x, 496.67, places=1)
        self.assertAlmostEqual(P[0].y, 556.67, places=1)
        self.assertAlmostEqual(P[1].x, 416.67, places=1)
        self.assertAlmostEqual(P[1].y, 416.67, places=1)
        self.assertAlmostEqual(P[2].x, 556.67, places=1)
        self.assertAlmostEqual(P[2].y, 436.67, places=1)

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

        self.assertAlmostEqual(P[0].x, 408.92, places=1)
        self.assertAlmostEqual(P[0].y, 539.17, places=1)
        self.assertAlmostEqual(P[1].x, 548.71, places=1)
        self.assertAlmostEqual(P[1].y, 407.21, places=1)
        self.assertAlmostEqual(P[2].x, 391.08, places=1)
        self.assertAlmostEqual(P[2].y, 260.83, places=1)
        self.assertAlmostEqual(P[3].x, 251.29, places=1)
        self.assertAlmostEqual(P[3].y, 392.79, places=1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 4)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), False)

        self.assertAlmostEqual(P[0].x, 408.92, places=1)
        self.assertAlmostEqual(P[0].y, 339.17, places=1)
        self.assertAlmostEqual(P[1].x, 451.29, places=1)
        self.assertAlmostEqual(P[1].y, 392.79, places=1)
        self.assertAlmostEqual(P[2].x, 391.08, places=1)
        self.assertAlmostEqual(P[2].y, 460.83, places=1)
        self.assertAlmostEqual(P[3].x, 348.71, places=1)
        self.assertAlmostEqual(P[3].y, 407.21, places=1)

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

        self.assertEqual(P[0].x, 50)
        self.assertEqual(P[0].y, 100)
        self.assertEqual(P[1].x, 50)
        self.assertEqual(P[1].y, 200)
        self.assertEqual(P[2].x, 100)
        self.assertEqual(P[2].y, 250)
        self.assertEqual(P[3].x, 200)
        self.assertEqual(P[3].y, 250)
        self.assertEqual(P[4].x, 250)
        self.assertEqual(P[4].y, 200)
        self.assertEqual(P[5].x, 250)
        self.assertEqual(P[5].y, 100)
        self.assertEqual(P[6].x, 200)
        self.assertEqual(P[6].y, 50)
        self.assertEqual(P[7].x, 100)
        self.assertEqual(P[7].y, 50)

if __name__ == '__main__':
    unittest.main()