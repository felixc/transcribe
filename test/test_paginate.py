import transcribe
import unittest


class PaginateTest(unittest.TestCase):
  def test_base_case(self):
    self.assertEqual(list(transcribe.paginate(2, [1, 2, 3, 4, 5])),
                     [(1, [1, 2]), (2, [3, 4]), (3, [5])])

  def test_items_smaller_than_page(self):
    self.assertEqual(list(transcribe.paginate(10, [1, 2])), [(1, [1, 2])])

  def test_empty_case(self):
    self.assertEqual(list(transcribe.paginate(3, [])), [])
