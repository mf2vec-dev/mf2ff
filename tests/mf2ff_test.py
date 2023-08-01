import unittest
from pathlib import Path

import fontforge

from mf2ff import Mf2ff


class Mf2ffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(__file__).parent
        try:
            cls.set_up_class() # test case specific class setup
        except AttributeError:
            # no test case specific class setup defined
            pass

    @classmethod
    def run_mf_file(cls, file_path, debug=False, options=None):
        '''run mf2ff on the file file_path in the test_inputs directory

        Args:
            file_path (str): relative path in the test_inputs directory to mf file
            debug (bool, optional): mf2ff's debug option. Defaults to False.
        '''
        cls.mf2ff = Mf2ff()
        cls.mf2ff.ppi = 72.27 # coordinates in mf are the same in font
        test_file_path = cls.test_dir / 'test_inputs' / file_path
        cls.mf2ff.input_file = str(test_file_path)
        cls.mf2ff.options['debug'] = bool(debug)
        if options is not None:
            cls.mf2ff.options.update(options)
        cls.mf2ff.run()
        cls.font = fontforge.open(str(test_file_path))
