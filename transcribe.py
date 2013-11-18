#!/usr/bin/python2.7
#
# Copyright 2013 Felix Crux (www.felixcrux.com)
# Released under the terms of the MIT (Expat) License (see LICENSE for details)
#

"""Generate static HTML from Django templates and YAML content."""


import argparse
import collections
import datetime
import imp
import json
import math
import os
import os.path
import shutil
import sys
import yaml

from django.conf import settings
import django.template
import django.template.loader
import django.utils.feedgenerator


DEFAULT_CONF = {
  'context': {},
  'content': os.path.join(os.getcwd(), 'content'),
  'templates': os.path.join(os.getcwd(), 'templates'),
  'output': os.path.join(os.getcwd(), 'out'),
  'static': [],
  'meta': {}
}

DEBUG = False  # Ugly, but I really don't want to thread conf['debug'] through
               # all the possible paths/layers that wind up at Context()


class RssFeed(django.utils.feedgenerator.Rss201rev2Feed):
  """Wrapper around Django's RSS feed class that uses transcribe's config."""
  def __init__(self, root, items, config, *args, **kwargs):
    super(RssFeed, self).__init__(
      title=config['title'],
      link=config['link'],
      description=config['desc'],
      *args, **kwargs)

    for item in items:
      self.add_item(
        title=item[config['item_title']],
        link=config['link'] + '/' + root + '/' + item['slug'],
        unique_id=item['slug'],
        pubdate=item[config['item_pub_date']],
        description=item[config['item_desc']] + '<p>Read more...</p>'
        # TODO: Get rid of that hardcoded 'Read more' string.
      )


class Context(django.template.Context):
  """Custom Django template context that includes extra helper variables."""

  _context = {}

  def __init__(self, root, content):
    content['root'] = root
    super(Context, self).__init__(dict(self._context.items() + content.items()))


def output_context_to_template(context, template_path, output_path):
  """Write the given context to the output path using a template.
     The 'template_path' parameter may be a list of templates to look for."""
  with open(output_path, 'w') as output:
    template_path = \
        template_path if type(template_path) == list else [template_path]
    template = django.template.loader.select_template(template_path)
    output.write(template.render(context).encode('UTF-8'))


def output_item(item, item_root, output_root):
  """Transcribe the given item to HTML using the appropriate template."""
  out_file_name = item['slug'] + '.html'
  template = os.path.join(item_root, 'item.html')
  specialized_template = os.path.join(item_root, out_file_name)
  output_context_to_template(
    Context(item_root, item),
    [specialized_template, template],
    os.path.join(output_root, out_file_name))


def output_archive(all_items, item_root, output_root, archive_by):
  """Arrange items into a date-based hierarchy and output to template."""
  # TODO: Get rid of this gross copy/sort hack.
  # TODO: Come up with a more sensible structure for the date hierarchy.
  archive = collections.defaultdict(lambda: collections.defaultdict(list))
  for item in all_items:
    date = item[archive_by]
    year = date.strftime('%Y')
    month = datetime.date(date.year, date.month, 1)
    archive[year][month].append(item)

  sorted_archive = []
  for year in archive:
    sorted_months = []
    for month in archive[year]:
      sorted_months.append({'month': month, 'posts': archive[year][month]})
    sorted_archive.append({'year': year, 'months': sorted_months})
    sorted_archive[-1]['months'].sort(key=lambda v: v['month'])
  sorted_archive.sort(key=lambda v: v['year'])

  archive_root = os.path.join(output_root, 'archives')
  os.mkdir(archive_root)
  output_context_to_template(
    Context(item_root, {'all_items': all_items, item_root: sorted_archive}),
    os.path.join(item_root, 'archive.html'),
    os.path.join(archive_root, 'index.html'))

  for year in set(item['year'] for item in sorted_archive):
    year_root = os.path.join(archive_root, str(year))
    year_items = [i for i in sorted_archive if i['year'] == year]
    os.mkdir(year_root)
    output_context_to_template(
      Context(item_root, {'all_items': all_items, item_root: year_items}),
      os.path.join(item_root, 'archive.html'),
      os.path.join(year_root, 'index.html'))
    for month in set(item['month'] for item in year_items[0]['months']):
      month_name = month.strftime('%b').lower()
      month_root = os.path.join(year_root, month_name)
      month_items = [i for i in year_items[0]['months'] if i['month'] == month]
      os.mkdir(month_root)
      output_context_to_template(
        Context(item_root, {
            'all_items': all_items,
            item_root: [{'year': year, 'months': month_items}]}),
        os.path.join(item_root, 'archive.html'),
        os.path.join(month_root, 'index.html'))


def output_linkables(all_items, item_root, output_root, linkable_attrs):
  """Write lists of items according to their linkable attributes."""
  # TODO: Shouldn't necessitate this kind of copy.
  linkables = collections.defaultdict(lambda: collections.defaultdict(list))

  for content in all_items:
    for attr in linkable_attrs:
      for attr_value in content[attr]:
        linkables[attr][attr_value].append(content)

  for attr in linkables:
    attr_root = os.path.join(output_root, attr)
    os.mkdir(attr_root)
    for attr_value in linkables[attr]:
      output_context_to_template(
        Context(item_root, {
            'context': 'Posts Tagged "' + attr_value + '"',
            item_root.split('/')[-1]: linkables[attr][attr_value]}),
        os.path.join(item_root, 'list.html'),
        os.path.join(attr_root, attr_value + '.html'))


def output_feed(all_items, item_root, output_root, config):
  """Produce an RSS feed of the items."""
  feed = RssFeed(item_root, all_items[:config['num_items']], config)
  with open(os.path.join(output_root, 'rss.xml'), 'w') as out_file:
    feed.write(out_file, 'utf-8')


def output_all(all_items, item_root, output_root, config):
  """Perform all of the templated output."""
  for item in all_items:
    output_item(item, item_root, output_root)

  if item_root in config:
    if 'order_by' in config[item_root]:
      all_items.sort(key=lambda v: v[config[item_root]['order_by']])
      all_items.reverse()
    if 'linkable_by' in config[item_root]:
      output_linkables(
        all_items, item_root, output_root, config[item_root]['linkable_by'])
    if 'archive_by' in config[item_root]:
      output_archive(
        all_items, item_root, output_root, config[item_root]['archive_by'])
    if 'feed' in config[item_root]:
      output_feed(all_items, item_root, output_root, config[item_root]['feed'])

    num_per_page = config[item_root].get('num_per_page', len(all_items))
    paginator = paginate(num_per_page, all_items)
    for page_num, items in paginator:
      output_context_to_template(
        Context(item_root, {
            'all_items': all_items,
            'page': page_num,
            'page_count': int(math.ceil(float(len(all_items)) / num_per_page)),
            item_root.split('/')[-1]: items}),
        os.path.join(item_root, 'list.html'),
        os.path.join(
          output_root,
          'index.html' if (page_num == 1) else str(page_num) + '.html'))


def paginate(size, items):
  """Generates (page-number, items) pairs given a page length and item list."""
  for i in xrange(0, len(items), size):
    yield (i / size + 1, items[i:i + size])


def recreate_dir(path):
  """Delete and recreate the given directory path."""
  shutil.rmtree(path, True)
  os.mkdir(path)


def generate_config(argv):
  """Returns the configuration to use based on all sources."""

  class AddToContextDictAction(argparse.Action):
    """Helper action for adding parsed arguments to the context dictionary."""
    def __call__(self, parser, namespace, values, option_string=None):
      new_context = {}
      if (namespace.context):
        new_context = dict(
          namespace.context.items() + [[values[0], json.loads(values[1])]])
      else:
        new_context = dict([[values[0], json.loads(values[1])]])
      setattr(namespace, 'context', new_context)

  config = DEFAULT_CONF

  arg_parser = argparse.ArgumentParser(
    description='Generate static HTML from Django templates and YAML content.')
  arg_parser.add_argument(
    '-cx', '--context', nargs=2, action=AddToContextDictAction,
    help='Extra context information to make available within your templates.')
  arg_parser.add_argument(
    '-i', '--content',
    help='Directory containing YAML input content.')
  arg_parser.add_argument(
    '-t', '--templates',
    help='Directory containing Django templates.')
  arg_parser.add_argument(
    '-o', '--output',
    help='Directory to write output to. Note: Contents are not preserved.')
  arg_parser.add_argument(
    '-s', '--static', action='append',
    help='Files/dirs that should be copied verbatim to output directory.')
  arg_parser.add_argument(
    '-c', '--config-file',
    help='Full path to the configuration file to use.')

  arg_conf = dict([(key, val) for key, val
                   in vars(arg_parser.parse_args(argv)).items()
                   if val is not None])

  if 'config_file' in arg_conf:
    config_dir = os.path.dirname(arg_conf['config_file'])
    config_file = os.path.basename(arg_conf['config_file'])
    if config_file[-3:] == '.py':
      config_file = config_file[:-3]
    file_handle, file_name, desc = imp.find_module(config_file, [config_dir])
    file_conf = imp.load_module(
      'transcribe_config', file_handle, file_name, desc
    ).TRANSCRIBE_CONFIG
    config = dict(config.items() + file_conf.items())
  config = dict(config.items() + arg_conf.items())

  Context._context = dict(Context._context.items() + config['context'].items())

  return config


def copy_static_content(sources, destination):
  """Perform a simple copy of files/dirs to the destination dir."""
  for content in sources:
    (shutil.copytree if os.path.isdir(content) else shutil.copy)(
      content, os.path.join(destination, os.path.basename(content)))


def main(argv):
  """Transcribe YAML content into HTML through Django templates."""

  conf = generate_config(argv)

  settings.configure(
    TEMPLATE_DIRS=(conf['templates'], ),
    TEMPLATE_LOADERS=(
      ('django.template.loaders.cached.Loader',
       ('django.template.loaders.filesystem.Loader', )), )
  )
  import django.contrib.syndication.views  # Requires Django to be configured.

  recreate_dir(conf['output'])
  copy_static_content(conf['static'], conf['output'])

  for root, _, files in os.walk(conf['content']):
    all_items = []

    item_root = os.path.relpath(root, conf['content'])
    output_root = os.path.join(conf['output'], item_root)
    if item_root != '.':
      os.mkdir(output_root)

    for file_name in files:
      content = yaml.load(open(os.path.join(root, file_name)))
      content['slug'] = os.path.splitext(file_name)[0]
      all_items.append(content)

    if all_items:
      output_all(all_items, item_root, output_root, conf['meta'])


if __name__ == '__main__':
  exit(main(sys.argv[1:]))
