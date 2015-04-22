#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2013–2015 Felix Crux <felixc@felixcrux.com>
# Released under the terms of the MIT (Expat) License (see LICENSE for details)
#

import tempfile
import unittest

import transcribe


class GenerateConfigurationTest(unittest.TestCase):
    def test_default_config(self):
        self.assertEqual(
            transcribe.DEFAULT_CONF, transcribe.generate_config([]))

    def test_file_overrides_defaults(self):
        conf_file = tempfile.NamedTemporaryFile(mode='w+t', suffix='.py')
        conf_file.write('TRANSCRIBE_CONFIG = { "output": "foo" }')
        conf_file.flush()
        result_conf = transcribe.generate_config(
            ['--config-file', conf_file.name])
        self.assertEqual(result_conf['output'], 'foo')

    def test_command_line_overrides_file(self):
        conf_file = tempfile.NamedTemporaryFile(mode='w+t', suffix='.py')
        conf_file.write('TRANSCRIBE_CONFIG = { "output": "foo" }')
        conf_file.flush()
        result_conf = transcribe.generate_config(
            ['--config-file', conf_file.name, '--output', 'bar'])
        self.assertEqual(result_conf['output'], 'bar')

    def test_command_line_overrides_defaults(self):
        test_conf = transcribe.DEFAULT_CONF.copy()
        test_conf.update({'content': 'foo'})
        self.assertEqual(
            test_conf,
            transcribe.generate_config(['--content', 'foo']))

    def test_add_context_vars(self):
        test_conf = transcribe.DEFAULT_CONF.copy()
        test_conf.update({'context': {
            'foo': 'bar',
            'baz': 23,
            'frob': [1, 2, 3]
        }})
        self.assertEqual(
            test_conf,
            transcribe.generate_config(
                ['--context', 'foo', '"bar"',
                 '-cx', 'baz', '23',
                 '-cx', 'frob', '[1, 2, 3]']))
