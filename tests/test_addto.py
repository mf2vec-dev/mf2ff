import unittest

from tests.mf2ff_test import Mf2ffTest


class TestAddto(Mf2ffTest):
    @classmethod
    def set_up_class(cls):
        cls.run_mf_file('test_addto/test_addto')

    def test_addto(self):
        g = self.font['A']
        bgl = g.layers[0]
        l = g.layers[1]
        self.assertEqual(bgl.isEmpty(), True)
        self.assertEqual(len(bgl), 0)
        self.assertEqual(l.isEmpty(), False)
        self.assertEqual(len(l), 2)

        c = l[0]

        # TODO

if __name__ == '__main__':
    unittest.main()
