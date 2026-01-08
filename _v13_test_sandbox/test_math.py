import math
import unittest
from math_utils import calculate_area

class TestMathUtils(unittest.TestCase):
    def test_calculate_area(self):
        radius = 5
        expected_area = math.pi * (radius ** 2)
        self.assertAlmostEqual(calculate_area(radius), expected_area, places=2)

if __name__ == '__main__':
    unittest.main()
