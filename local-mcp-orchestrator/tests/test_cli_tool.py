import io
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr


class TestCliTool(unittest.TestCase):
    def run_cli(self, argv):
        from src.cli_tool import main
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            try:
                code = main(argv)
            except SystemExit as e:
                code = int(e.code)
        return code, buf_out.getvalue().strip(), buf_err.getvalue().strip()

    def test_greet_default(self):
        code, out, err = self.run_cli(["greet"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "Hello, world!")
        self.assertEqual(err, "")

    def test_greet_named(self):
        code, out, err = self.run_cli(["greet", "--name", "Taro"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "Hello, Taro!")

    def test_add(self):
        code, out, err = self.run_cli(["add", "1", "2"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "3")

    def test_divide(self):
        code, out, err = self.run_cli(["divide", "4", "2"])
        self.assertEqual(code, 0)
        self.assertEqual(out, "2")

    def test_divide_by_zero(self):
        code, out, err = self.run_cli(["divide", "1", "0"])
        self.assertNotEqual(code, 0)
        self.assertIn("division by zero", err)


if __name__ == "__main__":
    unittest.main()

