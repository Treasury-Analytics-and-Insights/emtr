import sys
import unittest


sys.path.append('..')
from helpers import *

# test the str_to_ints function
class TestStringsToInt(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(str_to_ints(''), [])

    def test_single_number(self):
        self.assertEqual(str_to_ints('1'), [1])

    def test_single_number_with_spaces(self):
        self.assertEqual(str_to_ints(' 1 '), [1])

    def test_single_number_with_comma(self):
        self.assertEqual(str_to_ints('1,'), [1])

    def test_single_number_with_comma_and_spaces(self):
        self.assertEqual(str_to_ints(' 1 , '), [1])

    def test_two_numbers(self):
        self.assertEqual(str_to_ints('1,2'), [1, 2])

    def test_two_numbers_with_spaces(self):
        self.assertEqual(str_to_ints(' 1 , 2 '), [1, 2])

    def test_two_numbers_with_commas(self):
        self.assertEqual(str_to_ints('1,2,'), [1, 2])

    def test_two_numbers_with_commas_and_spaces(self):
        self.assertEqual(str_to_ints(' 1 , 2 , '), [1, 2])

    def test_two_numbers_with_commas_and_spaces_and_trailing_comma(self):
        self.assertEqual(str_to_ints(' 1 , 2 , , '), [1, 2])

    def test_two_numbers_with_commas_and_spaces_and_trailing_comma_and_spaces(self):
        self.assertEqual(str_to_ints(' 1 , 2 , , , '), [1, 2])

    def test_two_numbers_with_commas_and_spaces_and_trailing_comma_and_spaces_and_leading_comma(self):
        self.assertEqual(str_to_ints(' , 1 , 2 , , , '), [1, 2])

    def test_three_numbers(self):
        self.assertEqual(str_to_ints('1,2,3'), [1, 2, 3])


if __name__ == '__main__':
    unittest.main()

