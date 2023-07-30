import unittest

from tests.mf2ff_test import Mf2ffTest


class TestCulling(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_culling/test_culling')

    def test_cull_1_inf(self):
        g = self.font['A']
        l = g.layers[1]
        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 1)

        c = l[0]
        P = [p for p in c if p.on_curve]

        self.assertEqual(len(P), 8)
        self.assertEqual(c.closed, True)
        self.assertEqual(c.isClockwise(), True)

        self.assertEqual(P[0].x, 100)
        self.assertEqual(P[0].y, 100)
        self.assertEqual(P[1].x, 100)
        self.assertEqual(P[1].y, 300)
        self.assertEqual(P[2].x, 200)
        self.assertEqual(P[2].y, 300)
        self.assertEqual(P[3].x, 200)
        self.assertEqual(P[3].y, 400)
        self.assertEqual(P[4].x, 400)
        self.assertEqual(P[4].y, 400)
        self.assertEqual(P[5].x, 400)
        self.assertEqual(P[5].y, 200)
        self.assertEqual(P[6].x, 300)
        self.assertEqual(P[6].y, 200)
        self.assertEqual(P[7].x, 300)
        self.assertEqual(P[7].y, 100)

    def test_cull_1_1(self):
        self.fail('result of glyph B not OK')

if __name__ == '__main__':
    unittest.main()