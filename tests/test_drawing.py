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

    def test_line_penrazor_right(self):
        g = self.font['a']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 4)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertAlmostEqual(P[0].x, 24.330, places=1)
        self.assertEqual(P[0].y, 22.5)
        self.assertAlmostEqual(P[1].x, 64.330, places=1)
        self.assertEqual(P[1].y, 22.5)
        self.assertAlmostEqual(P[2].x, 55.670, places=1)
        self.assertEqual(P[2].y, 17.5)
        self.assertAlmostEqual(P[3].x, 15.670, places=1)
        self.assertEqual(P[3].y, 17.5)

    def test_line_penrazor_left(self):
        g = self.font['b']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 4)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertAlmostEqual(P[0].x, 64.330, places=1)
        self.assertEqual(P[0].y, 22.5)
        self.assertAlmostEqual(P[1].x, 55.670, places=1)
        self.assertEqual(P[1].y, 17.5)
        self.assertAlmostEqual(P[2].x, 15.670, places=1)
        self.assertEqual(P[2].y, 17.5)
        self.assertAlmostEqual(P[3].x, 24.330, places=1)
        self.assertEqual(P[3].y, 22.5)

    def test_open_penrazor(self):
        g = self.font['c']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 10)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertAlmostEqual(P[0].x, 19.330, places=1)
        self.assertEqual(P[0].y, 82.5)
        self.assertAlmostEqual(P[1].x, 94.330, places=1)
        self.assertEqual(P[1].y, 22.5)
        self.assertAlmostEqual(P[2].x, 85.670, places=1)
        self.assertEqual(P[2].y, 17.5)
        self.assertAlmostEqual(P[3].x, 5.670, places=1)
        self.assertEqual(P[3].y, 7.5)
        self.assertAlmostEqual(P[4].x, 14.330, places=1)
        self.assertEqual(P[4].y, 12.5)
        self.assertAlmostEqual(P[5].x, 81.435, places=1)
        self.assertAlmostEqual(P[5].y, 20.888, places=1)
        self.assertAlmostEqual(P[6].x, 19.330, places=1)
        self.assertAlmostEqual(P[6].y, 70.572, places=1)
        self.assertAlmostEqual(P[7].x, 19.330, places=1)
        self.assertEqual(P[7].y, 22.5)
        self.assertAlmostEqual(P[8].x, 10.670, places=1)
        self.assertEqual(P[8].y, 17.5)
        self.assertAlmostEqual(P[9].x, 10.670, places=1)
        self.assertEqual(P[9].y, 77.5)

    def test_almost_overlap_penrazor(self):
        g = self.font['d']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 10)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertAlmostEqual(P[0].x, 19.330, places=1)
        self.assertEqual(P[0].y, 82.5)
        self.assertAlmostEqual(P[1].x, 94.330, places=1)
        self.assertEqual(P[1].y, 22.5)
        self.assertAlmostEqual(P[2].x, 85.670, places=1)
        self.assertEqual(P[2].y, 17.5)
        self.assertAlmostEqual(P[3].x, 5.670, places=1)
        self.assertEqual(P[3].y, 7.5)
        self.assertAlmostEqual(P[4].x, 14.330, places=1)
        self.assertEqual(P[4].y, 12.5)
        self.assertAlmostEqual(P[5].x, 81.435, places=1)
        self.assertAlmostEqual(P[5].y, 20.888, places=1)
        self.assertAlmostEqual(P[6].x, 19.330, places=1)
        self.assertAlmostEqual(P[6].y, 70.572, places=1)
        self.assertAlmostEqual(P[7].x, 19.330, places=1)
        self.assertEqual(P[7].y, 15.5)
        self.assertAlmostEqual(P[8].x, 10.670, places=1)
        self.assertEqual(P[8].y, 10.5)
        self.assertAlmostEqual(P[9].x, 10.670, places=1)
        self.assertEqual(P[9].y, 77.5)

    def test_just_overlap_penrazor(self):
        g = self.font['e']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 2)

        c = l[0] # outer
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 6)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertAlmostEqual(P[0].x, 19.330, places=1)
        self.assertEqual(P[0].y, 82.5)
        self.assertAlmostEqual(P[1].x, 94.330, places=1)
        self.assertEqual(P[1].y, 22.5)
        self.assertAlmostEqual(P[2].x, 85.670, places=1)
        self.assertEqual(P[2].y, 17.5)
        self.assertAlmostEqual(P[3].x, 5.670, places=1)
        self.assertEqual(P[3].y, 7.5)
        self.assertAlmostEqual(P[4].x, 10.670, places=1)
        self.assertAlmostEqual(P[4].y, 10.387, places=1)
        self.assertAlmostEqual(P[5].x, 10.670, places=1)
        self.assertEqual(P[5].y, 77.5)

        c = l[1] # inner
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 4)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), False)
        
        self.assertAlmostEqual(P[0].x, 19.330, places=1)
        self.assertAlmostEqual(P[0].y, 70.572, places=1)
        self.assertAlmostEqual(P[1].x, 19.330, places=1)
        self.assertEqual(P[1].y, 14.5)
        self.assertAlmostEqual(P[2].x, 16.290, places=1)
        self.assertAlmostEqual(P[2].y, 12.765, places=1)
        self.assertAlmostEqual(P[3].x, 81.435, places=1)
        self.assertAlmostEqual(P[3].y, 20.888, places=1)

    def test_just_crossing_penrazor(self):
        g = self.font['f']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 2)

        c = l[0] # outer
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 9)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertAlmostEqual(P[0].x, 19.330, places=1)
        self.assertEqual(P[0].y, 82.5)
        self.assertAlmostEqual(P[1].x, 94.330, places=1)
        self.assertEqual(P[1].y, 22.5)
        self.assertAlmostEqual(P[2].x, 85.670, places=1)
        self.assertEqual(P[2].y, 17.5)
        self.assertAlmostEqual(P[3].x, 12.052, places=1)
        self.assertAlmostEqual(P[3].y, 8.298, places=1)
        self.assertAlmostEqual(P[4].x, 10.670, places=1)
        self.assertEqual(P[4].y, 7.5)
        self.assertAlmostEqual(P[5].x, 10.670, places=1)
        self.assertEqual(P[5].y, 8.125)
        self.assertAlmostEqual(P[6].x, 5.670, places=1)
        self.assertEqual(P[6].y, 7.5)
        self.assertAlmostEqual(P[7].x, 10.670, places=1)
        self.assertAlmostEqual(P[7].y, 10.387, places=1)
        self.assertAlmostEqual(P[8].x, 10.670, places=1)
        self.assertEqual(P[8].y, 77.5)

        c = l[1] # inner
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 3)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), False)
        
        self.assertAlmostEqual(P[0].x, 19.330, places=1)
        self.assertAlmostEqual(P[0].y, 70.572, places=1)
        self.assertAlmostEqual(P[1].x, 19.330, places=1)
        self.assertAlmostEqual(P[1].y, 13.125, places=1)
        self.assertAlmostEqual(P[2].x, 81.435, places=1)
        self.assertAlmostEqual(P[2].y, 20.888, places=1)

    def test_crossing_penrazor(self):
        g = self.font['g']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 2)

        c = l[0] # outer
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 10)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertAlmostEqual(P[0].x, 19.330, places=1)
        self.assertEqual(P[0].y, 82.5)
        self.assertAlmostEqual(P[1].x, 94.330, places=1)
        self.assertEqual(P[1].y, 22.5)
        self.assertAlmostEqual(P[2].x, 85.670, places=1)
        self.assertEqual(P[2].y, 17.5)
        self.assertAlmostEqual(P[3].x, 19.330, places=1)
        self.assertAlmostEqual(P[3].y, 9.207, places=1)
        self.assertAlmostEqual(P[4].x, 19.330, places=1)
        self.assertEqual(P[4].y, 2.5)
        self.assertAlmostEqual(P[5].x, 10.670, places=1)
        self.assertEqual(P[5].y, -2.5)
        self.assertAlmostEqual(P[6].x, 10.670, places=1)
        self.assertEqual(P[6].y, 8.125)
        self.assertAlmostEqual(P[7].x, 5.670, places=1)
        self.assertEqual(P[7].y, 7.5)
        self.assertAlmostEqual(P[8].x, 10.670, places=1)
        self.assertAlmostEqual(P[8].y, 10.387, places=1)
        self.assertAlmostEqual(P[9].x, 10.670, places=1)
        self.assertEqual(P[9].y, 77.5)

        c = l[1] # inner
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 3)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), False)
        
        self.assertAlmostEqual(P[0].x, 19.330, places=1)
        self.assertAlmostEqual(P[0].y, 70.572, places=1)
        self.assertAlmostEqual(P[1].x, 19.330, places=1)
        self.assertAlmostEqual(P[1].y, 13.125, places=1)
        self.assertAlmostEqual(P[2].x, 81.435, places=1)
        self.assertAlmostEqual(P[2].y, 20.888, places=1)

    def test_closed_penrazor(self):
        g = self.font['h']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 2)

        c = l[0] # outer
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 5)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertAlmostEqual(P[0].x, 19.330, places=1)
        self.assertEqual(P[0].y, 82.5)
        self.assertAlmostEqual(P[1].x, 94.330, places=1)
        self.assertEqual(P[1].y, 22.5)
        self.assertAlmostEqual(P[2].x, 85.670, places=1)
        self.assertEqual(P[2].y, 17.5)
        self.assertAlmostEqual(P[3].x, 5.670, places=1)
        self.assertEqual(P[3].y, 7.5)
        self.assertAlmostEqual(P[4].x, 10.670, places=1)
        self.assertEqual(P[4].y, 77.5)

        c = l[1] # inner
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 3)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), False)

        self.assertAlmostEqual(P[0].x, 18.524, places=1)
        self.assertAlmostEqual(P[0].y, 71.217, places=1)
        self.assertAlmostEqual(P[1].x, 14.330, places=1)
        self.assertAlmostEqual(P[1].y, 12.5, places=1)
        self.assertAlmostEqual(P[2].x, 81.435, places=1)
        self.assertAlmostEqual(P[2].y, 20.888, places=1)

    def test_curve_1_penrazor(self):
        g = self.font['i']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 8)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)
        
        self.assertAlmostEqual(P[0].x, 24.330, places=1)
        self.assertEqual(P[0].y, 22.5)
        self.assertAlmostEqual(P[1].x, 15.670, places=1)
        self.assertEqual(P[1].y, 17.5)
        self.assertAlmostEqual(P[2].x, 25.670, places=1)
        self.assertAlmostEqual(P[2].y, 37.499, places=1)
        self.assertAlmostEqual(P[3].x, 22.319, places=1)
        self.assertAlmostEqual(P[3].y, 50.000, places=1)
        self.assertAlmostEqual(P[4].x, 15.670, places=1)
        self.assertEqual(P[4].y, 57.5)
        self.assertAlmostEqual(P[5].x, 24.330, places=1)
        self.assertEqual(P[5].y, 62.5)
        self.assertAlmostEqual(P[6].x, 30.980, places=1)
        self.assertAlmostEqual(P[6].y, 55.000, places=1)
        self.assertAlmostEqual(P[7].x, 34.330, places=1)
        self.assertAlmostEqual(P[7].y, 42.499, places=1)

        P = [p for p in c if not p.on_curve] # control points
        self.assertEqual(len(P), 12)
        
        self.assertAlmostEqual(P[0].x, 21.965, places=1)
        self.assertAlmostEqual(P[0].y, 22.222, places=1)
        self.assertAlmostEqual(P[1].x, 25.670, places=1)
        self.assertAlmostEqual(P[1].y, 29.631, places=1)
        self.assertAlmostEqual(P[2].x, 25.670, places=1)
        self.assertAlmostEqual(P[2].y, 41.947, places=1)
        self.assertAlmostEqual(P[3].x, 24.486, places=1)
        self.assertAlmostEqual(P[3].y, 46.249, places=1)
        self.assertAlmostEqual(P[4].x, 20.653, places=1)
        self.assertAlmostEqual(P[4].y, 52.887, places=1)
        self.assertAlmostEqual(P[5].x, 18.406, places=1)
        self.assertAlmostEqual(P[5].y, 55.447, places=1)
        self.assertAlmostEqual(P[6].x, 27.066, places=1)
        self.assertAlmostEqual(P[6].y, 60.447, places=1)
        self.assertAlmostEqual(P[7].x, 29.314, places=1)
        self.assertAlmostEqual(P[7].y, 57.887, places=1)
        self.assertAlmostEqual(P[8].x, 33.146, places=1)
        self.assertAlmostEqual(P[8].y, 51.249, places=1)
        self.assertAlmostEqual(P[9].x, 34.329, places=1)
        self.assertAlmostEqual(P[9].y, 46.947, places=1)
        self.assertAlmostEqual(P[10].x, 34.330, places=1)
        self.assertAlmostEqual(P[10].y, 34.631, places=1)
        self.assertEqual(P[11].x, 30.625)
        self.assertAlmostEqual(P[11].y, 27.222, places=1)

    def test_curve_2_penrazor(self):
        g = self.font['j']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 9)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)
        
        self.assertEqual(P[0].x, 22.5)
        self.assertAlmostEqual(P[0].y, 15.670, places=1)
        self.assertEqual(P[1].x, 17.5)
        self.assertAlmostEqual(P[1].y, 24.330, places=1)
        self.assertEqual(P[2].x, 27.5)
        self.assertAlmostEqual(P[2].y, 44.330, places=1)
        self.assertAlmostEqual(P[3].x, 26.213, places=1)
        self.assertAlmostEqual(P[3].y, 52.248, places=1)
        self.assertEqual(P[4].x, 22.5)
        self.assertAlmostEqual(P[4].y, 55.670, places=1)
        self.assertEqual(P[5].x, 17.5)
        self.assertAlmostEqual(P[5].y, 64.330, places=1)
        self.assertAlmostEqual(P[6].x, 24.149, places=1)
        self.assertAlmostEqual(P[6].y, 56.831, places=1)
        self.assertAlmostEqual(P[7].x, 29.149, places=1)
        self.assertAlmostEqual(P[7].y, 48.171, places=1)
        self.assertEqual(P[8].x, 32.5)
        self.assertAlmostEqual(P[8].y, 35.670, places=1)

    # TODO output of self.font['k'] is corrupted by FontForge' removeOverlap()

    def test_parallel_penrazor(self):
        # path parallel to penrazor
        g = self.font['l']
        l = g.layers[1]

        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 7)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)
        
        self.assertEqual(P[0].x, 65)
        self.assertEqual(P[0].y, 60)
        self.assertEqual(P[1].x, 65)
        self.assertEqual(P[1].y, 20)
        self.assertEqual(P[2].x, 55)
        self.assertEqual(P[2].y, 20)
        self.assertEqual(P[3].x, 55)
        self.assertEqual(P[3].y, 50)
        self.assertEqual(P[4].x, 25)
        self.assertEqual(P[4].y, 20)
        self.assertEqual(P[5].x, 15)
        self.assertEqual(P[5].y, 20)
        self.assertEqual(P[6].x, 55)
        self.assertEqual(P[6].y, 60)

if __name__ == '__main__':
    unittest.main()
