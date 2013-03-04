import os
import os.path
import shutil
import tempfile
import unittest

import transcribe


class CopyStaticContentTest(unittest.TestCase):
  def test_copy_nothing(self):
    try:
      out_dir = tempfile.mkdtemp()
      transcribe.copy_static_content([], out_dir)
      # No exceptions thrown? Good.
    finally:
      shutil.rmtree(out_dir)

  def test_copy_file(self):
    try:
      out_dir = tempfile.mkdtemp()
      test_file = tempfile.NamedTemporaryFile()
      transcribe.copy_static_content([test_file.name], out_dir)
      self.assertEqual(os.listdir(out_dir), [os.path.basename(test_file.name)])
    finally:
      shutil.rmtree(out_dir)

  def test_copy_dir(self):
    try:
      out_dir = tempfile.mkdtemp()
      test_dir = tempfile.mkdtemp()
      transcribe.copy_static_content([test_dir], out_dir)
      self.assertEqual(os.listdir(out_dir), [os.path.split(test_dir)[1]])
    finally:
      shutil.rmtree(out_dir)
      shutil.rmtree(test_dir)

  def test_copy_multiple_items(self):
    try:
      out_dir = tempfile.mkdtemp()
      test_dir = tempfile.mkdtemp()
      test_file = tempfile.NamedTemporaryFile()
      transcribe.copy_static_content([test_dir, test_file.name], out_dir)
      self.assertEqual(
        os.listdir(out_dir),
        [os.path.basename(test_file.name), os.path.split(test_dir)[1]])
    finally:
      shutil.rmtree(out_dir)
      shutil.rmtree(test_dir)
