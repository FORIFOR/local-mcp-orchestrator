import unittest


class TestCalc(unittest.TestCase):
    def test_divide_integers(self):
        from src.calc import divide
        self.assertEqual(divide(4, 2), 2)
        self.assertEqual(divide(-9, 3), -3)

    def test_divide_by_zero_raises_value_error(self):
        from src.calc import divide
        with self.assertRaises(ValueError):
            divide(1, 0)


if __name__ == "__main__":
    unittest.main()

