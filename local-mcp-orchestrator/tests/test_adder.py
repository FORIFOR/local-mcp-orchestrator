import unittest


class TestAdder(unittest.TestCase):
    def test_add_integers(self):
        from src.adder import add
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(-1, 5), 4)
        self.assertEqual(add(0, 0), 0)

    def test_add_floats(self):
        from src.adder import add
        self.assertAlmostEqual(add(0.1, 0.2), 0.3, places=6)


if __name__ == "__main__":
    unittest.main()

