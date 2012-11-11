#!/usr/bin/python2.7
#
# Copyright (c) 2012 Felix Crux (www.felixcrux.com)
# Released under the terms of the MIT License (see README for details).
#

"""Generate static HTML from Django templates and YAML content."""


# TODO: Move strings into constants where appropriate (most places).
# TODO: Test -- that is, other than in production...


import argparse
import collections
import datetime
import imp
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


class RssFeed(django.utils.feedgenerator.Rss201rev2Feed):
  """Wrapper around Django's RSS feed class that uses transcribe.py's config."""
  def __init__(self, root, items, *args, **kwargs):
    super(RssFeed, self).__init__(
      title = conf.META[root]['feed']['title'],
      link = conf.META[root]['feed']['link'],
      description = conf.META[root]['feed']['desc'],
      *args, **kwargs)

    for item in items:
      self.add_item(
        title = item[conf.META[root]['feed']['item_title']],
        link =
            conf.META[root]['feed']['link'] + '/' + root + '/' + item['slug'],
        description =
            item[conf.META[root]['feed']['item_desc']] + '<p>Read more...</p>'
            # TODO: Get rid of that hardcoded 'Read more' string.
      )


class Context(django.template.Context):
  """Custom Django template context that includes extra helper variables."""
  def __init__(self, root, content):
    content['debug'] = conf.DEBUG
    content['root'] = root
    super(Context, self).__init__(content)


def output_context_to_template(context, template_path, output_path):
  """Write the given context to the output path using a template.
     The 'template_path' parameter may be a list of templates to look for."""
  with open(output_path, 'w') as output:
    template_path = \
        template_path if type(template_path) == list else [template_path]
    template = django.template.loader.select_template(template_path)
    output.write(template.render(context).encode('UTF-8'))


def output_item(item, item_root, output_root):
  """Transcribe the given item to output HTML using the appropriate template."""
  out_file_name = item['slug'] + '.html'
  template = os.path.join(item_root, 'item.html')
  specialized_template = os.path.join(item_root, out_file_name)
  output_context_to_template(
    Context(item_root, item),
    [specialized_template, template],
    os.path.join(output_root, out_file_name))


def output_archive(all_items, item_root, output_root):
  """Arrange items into a date-based hierarchy and output to template."""
  # TODO: Get rid of this gross copy/sort hack.
  # TODO: Come up with a more sensible structure for the date hierarchy.
  archive_by = conf.META[item_root]['archive_by']
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
      sorted_months.append({ 'month': month, 'posts': archive[year][month] })
    sorted_archive.append({ 'year': year, 'months': sorted_months })
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
    year_items = filter(lambda i: i['year'] == year, sorted_archive)
    os.mkdir(year_root)
    output_context_to_template(
      Context(item_root, {'all_items': all_items, item_root: year_items}),
      os.path.join(item_root, 'archive.html'),
      os.path.join(year_root, 'index.html'))
    for month in set(item['month'] for item in year_items[0]['months']):
      month_name = month.strftime('%b').lower()
      month_root = os.path.join(year_root, month_name)
      month_items = filter(
        lambda i: i['month'] == month, year_items[0]['months'])
      os.mkdir(month_root)
      output_context_to_template(
        Context(item_root, {
            'all_items': all_items,
            item_root: [{'year': year, 'months': month_items}]}),
        os.path.join(item_root, 'archive.html'),
        os.path.join(month_root, 'index.html'))


def output_linkables(all_items, item_root, output_root):
  """Write lists of items according to their linkable attributes."""
  # TODO: Shouldn't necessitate this kind of copy.
  linkables = collections.defaultdict(lambda: collections.defaultdict(list))

  for content in all_items:
    for attr in conf.META[item_root]['linkable_by']:
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


def output_feed(all_items, item_root, output_root):
  """Produce an RSS feed of the items."""
  feed = RssFeed(
    item_root,
    all_items[:conf.META[item_root]['feed']['num_items']])
  with open(os.path.join(output_root, 'rss.xml'), 'w') as fp:
    feed.write(fp, 'utf-8')


def output_all(all_items, item_root, output_root):
  """Perform all of the templated output."""
  for item in all_items:
    output_item(item, item_root, output_root)

  if item_root in conf.META:
    if 'order_by' in conf.META[item_root]:
      all_items.sort(key=lambda v: v[conf.META[item_root]['order_by']])
      all_items.reverse()
    if 'linkable_by' in conf.META[item_root]:
      output_linkables(all_items, item_root, output_root)
    if 'archive_by' in conf.META[item_root]:
      output_archive(all_items, item_root, output_root)
    if 'feed' in conf.META[item_root]:
      output_feed(all_items, item_root, output_root)

    num_per_page = conf.META[item_root].get('num_per_page', len(all_items))
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
    yield (i/size + 1, items[i:i+size])


def recreate_dir(path):
  """Delete and recreate the given directory path."""
  shutil.rmtree(path, True)
  os.mkdir(path)


def generate_configuration(argv):
  """Returns the config to use based on the config file and invocation params."""

  arg_parser = argparse.ArgumentParser(
    description='Generate static HTML from Django templates and YAML content.',
    epilog='All arguments are required, but they may be provided in a ' +
      'configuration file instead. See the included sample for details.')
  arg_parser.add_argument(
    '-d', '--debug', type=bool, dest='DEBUG',
    help='Sets the "debug" variable for use in templates.'
  )
  arg_parser.add_argument(
    '-c', '--content', dest='CONTENT',
    help='Directory containing YAML content.'
  )
  arg_parser.add_argument(
    '-t', '--templates', dest='TEMPLATES',
    help='Directory containing Django templates.'
  )
  arg_parser.add_argument(
    '-o', '--output', dest='OUTPUT',
    help='Directory to write output to. Note: Contents are not preserved.'
  )
  arg_parser.add_argument(
    '-s', '--static', action='append', dest='STATIC',
    help='Files/directories that should be copied verbatim to output directory.',
  )
  arg_parser.add_argument(
    'configfile', nargs='?', default='transcribe_config',
    help='Full path to the configuration file to use.'
  )
  config = arg_parser.parse_args(argv)
  config.META = {}

  config_dir = os.path.dirname(config.configfile)
  config_file = os.path.basename(config.configfile)
  if config_file[-3:] == '.py':
    config_file = config_file[:-3]
  try:
    fh, fn, desc = imp.find_module(config_file, [config_dir])
    file_config = imp.load_module('transcribe_config', fh, fn, desc)
  except ImportError:
    file_config = config

  if not config.DEBUG:
    config.DEBUG = file_config.DEBUG if file_config.DEBUG else False
  if not config.CONTENT:
    config.CONTENT = file_config.CONTENT if file_config.CONTENT else 'content'
  if not config.TEMPLATES:
    config.TEMPLATES = file_config.TEMPLATES if file_config.TEMPLATES else 'templates'
  if not config.OUTPUT:
    config.OUTPUT = file_config.OUTPUT if file_config.OUTPUT else 'out'
  if not config.STATIC:
    config.STATIC = file_config.STATIC if file_config.STATIC else []
  if file_config.META:
    config.META = file_config.META

  return config


def copy_static_content(sources, destination):
  """Perform a simple copy of files/dirs to the destination dir."""
  for content in sources:
    (shutil.copytree if os.path.isdir(content) else shutil.copy)(
      content, os.path.join(destination, os.path.basename(content)))


def main(argv):
  """Transcribe YAML content into HTML through Django templates."""

  global conf
  conf = generate_configuration(argv)

  settings.configure(
    TEMPLATE_DIRS = (conf.TEMPLATES, ),
    TEMPLATE_LOADERS = (
      ('django.template.loaders.cached.Loader',
       ('django.template.loaders.filesystem.Loader', )), )
    )
  import django.contrib.syndication.views  # Requires Django to be configured.

  recreate_dir(conf.OUTPUT)
  copy_static_content(conf.STATIC, conf.OUTPUT)

  for root, dirs, files in os.walk(conf.CONTENT):
    all_items = []

    item_root = os.path.relpath(root, conf.CONTENT)
    output_root = os.path.join(conf.OUTPUT, item_root)
    if item_root != '.':
      os.mkdir(output_root)

    for file_name in files:
      content = yaml.load(open(os.path.join(root, file_name)))
      content['slug'] = os.path.splitext(file_name)[0]
      all_items.append(content)

    if all_items:
      output_all(all_items, item_root, output_root)


if __name__ == '__main__':
  exit(main(sys.argv[1:]))
