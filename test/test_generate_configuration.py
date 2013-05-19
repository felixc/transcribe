import tempfile
import unittest

import transcribe


class GenerateConfigurationTest(unittest.TestCase):
  def test_default_config(self):
    self.assertEqual(transcribe.DEFAULT_CONF, transcribe.generate_config([]))

  def test_file_overrides_defaults(self):
    conf_file = tempfile.NamedTemporaryFile(suffix='.py')
    conf_file.write('TRANSCRIBE_CONFIG = { "output": "foo" }')
    conf_file.flush()
    result_conf = transcribe.generate_config(['--config-file', conf_file.name])
    self.assertEqual(result_conf['output'], 'foo')

  def test_command_line_overrides_file(self):
    conf_file = tempfile.NamedTemporaryFile(suffix='.py')
    conf_file.write('TRANSCRIBE_CONFIG = { "output": "foo" }')
    conf_file.flush()
    result_conf = transcribe.generate_config(
      ['--config-file', conf_file.name, '--output', 'bar'])
    self.assertEqual(result_conf['output'], 'bar')

  def test_command_line_overrides_defaults(self):
    self.assertEqual(
      dict(transcribe.DEFAULT_CONF.items() + {'content': 'foo'}.items()),
      transcribe.generate_config(['--content', 'foo']))

  def test_add_context_vars(self):
    self.assertEqual(
      dict(transcribe.DEFAULT_CONF.items() + {'context': {
          'foo': 'bar',
          'baz': 23,
          'frob': [1, 2, 3]
        }}.items()),
      transcribe.generate_config(
        ['--context', 'foo', '"bar"',
         '-cx', 'baz', '23',
         '-cx', 'frob', '[1, 2, 3]']))
