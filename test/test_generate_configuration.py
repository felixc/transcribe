import tempfile
import unittest

import transcribe


class GenerateConfigurationTest(unittest.TestCase):
  def test_default_config(self):
    self.assertEqual(transcribe.DEFAULT_CONF, transcribe.generate_config([]))

  def test_file_overrides_defaults(self):
    conf_file = tempfile.NamedTemporaryFile(suffix='.py')
    conf_file.write('TRANSCRIBE_CONFIG = { "debug": True, "output": "foo" }')
    conf_file.flush()
    result_conf = transcribe.generate_config(['--config-file', conf_file.name])
    self.assertTrue(result_conf['debug'])
    self.assertEqual(result_conf['output'], 'foo')

  def test_command_line_overrides_file(self):
    conf_file = tempfile.NamedTemporaryFile(suffix='.py')
    conf_file.write('TRANSCRIBE_CONFIG = { "debug": True, "output": "foo" }\n')
    conf_file.flush()
    result_conf = transcribe.generate_config(
      ['--config-file', conf_file.name, '--no-debug', '--output', 'bar'])
    self.assertFalse(result_conf['debug'])
    self.assertEqual(result_conf['output'], 'bar')

  def test_command_line_overrides_defaults(self):
    self.assertEqual(
      dict(transcribe.DEFAULT_CONF.items() + {'debug': True}.items()),
      transcribe.generate_config(['--debug']))
