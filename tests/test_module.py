import platform
import subprocess
import unittest


class TestModule(unittest.TestCase):
    def test_call_on_command_line(self):
        if platform.system() == 'Windows':
            exit_code = subprocess.call(['ffpython', '-m', 'mf2ff', '-version'], stdout=subprocess.DEVNULL)
        else:
            exit_code = subprocess.call(['python3', '-m', 'mf2ff', '-version'], stdout=subprocess.DEVNULL)
        self.assertEqual(exit_code, 0)

    def test_import_f2ff_module(self):
        try:
            import mf2ff
        except ModuleNotFoundError:
            self.fail('importing mf2ff failed')

    def test_module_version_is_string(self):
        import mf2ff
        self.assertIsInstance(mf2ff.__version__, str)

    # missing tests:
    # - chck if all font options work
    # - check if help is printed.

if __name__ == '__main__':
    unittest.main()
