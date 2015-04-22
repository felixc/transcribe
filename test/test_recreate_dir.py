#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2013–2015 Felix Crux <felixc@felixcrux.com>
# Released under the terms of the MIT (Expat) License (see LICENSE for details)
#

import os
import os.path
import shutil
import tempfile
import unittest
import uuid

import transcribe


class RecreateDirTest(unittest.TestCase):
    def test_nonexistent_dir(self):
        try:
            test_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
            transcribe.recreate_dir(test_dir)
            self.assertTrue(os.path.isdir(test_dir))
        finally:
            shutil.rmtree(test_dir)

    def test_dir_with_contents(self):
        try:
            test_dir = tempfile.mkdtemp()
            tempfile.mkstemp(dir=test_dir)
            self.assertNotEqual(os.listdir(test_dir), [])
            transcribe.recreate_dir(test_dir)
            self.assertEqual(os.listdir(test_dir), [])
        finally:
            shutil.rmtree(test_dir)
