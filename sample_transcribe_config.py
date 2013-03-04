#
# Sample configuration file for transcribe.py.
#
# Edit this file to suit your needs, then save it as 'transcribe_config.py' in
# the same directory as 'transcribe.py', or somewhere else on PYTHONPATH.
#
# Copyright 2013 Felix Crux (www.felixcrux.com)
# Released under the terms of the MIT License (see README for details).
#


TRANSCRIBE_CONFIG = {

  # No inherent meaning, but useful for your own templates where you may wish
  # to selectively include/exclude content based on this setting. Available in
  # templates as the variable 'debug'.
  'debug': False,

  # content, templates, and output are the directories that contain your YAML
  # content, your Django templates, and the generated output, respectively.
  'content': '/home/me/my-site/content',
  'templates': '/home/me/my-site/templates',
  'output': '/home/me/my-site/out', # NOTE: Everything in this directory will
                                    # be deleted every time the tool is run!

  # Files or directories that should be copied verbatim to the output directory.
  # Useful for non-templated HTML, CSS, JavaScript, etc.
  'static': ['/home/me/my-site/css', '/home/me/my-site/404.html'],


  # Configuration for all the "special" aspects of the content.
  # The example below assumes a series of YAML files under 'content/blog',
  # with a format similar to:
  #
  #   title: "An example YAML content file."
  #   author: ["J. Doe"]
  #   pub_date: !!timestamp 2012-10-01
  #   tags: ["example", "configuration"]
  #   summary: "An article published to example.com through transcribe.py"
  #
  # If we assume the above file is named 'an-example-yaml-content-file.yaml', it
  # would show up under 'output/blog/an-example-yaml-content-file.html' after
  # processing, using the 'templates/blog/item.html' template. In addition, if
  # the 'templates/blog/list.html' template exists, an additional file,
  # 'output/blog/index.html', would be created, listing the above file and any
  # others that may be present in the same directory.
  #
  # The base name of the file (i.e. 'an-example-yaml-content-file') is known as
  # the 'slug' of the item, and is available as a template variable. It can also
  # be used in the configuration below, e.g. you could set 'order_by': 'slug'.
  # (https://secure.wikimedia.org/wikipedia/en/wiki/Slug_%28web_publishing%29)
  #
  # Note that 'blog' in the example above is not at all special, it's just the
  # directory name chosen for the example.
  'meta': {
    # Each directory under content gets its own entry.
    'blog': {
       # Generates a series of overview pages, one for each linkable attribute
       # value seen, where each page links to every item that contains that
       # value.  Note that linkable attributes must be given as lists, even when
       # they only contain one value (see "author" in the example above).  Uses
       # the template 'templates/*/list.html'.
       'linkable_by': ['author', 'tags'],
       # Attribute to use as the basis for a chronological archive.
       # Must be a !!timestamp value.
       # Uses the template 'templates/*/archive.html'.
       'archive_by': 'pub_date',
       # In listings, which attribute should items be ordered by. Often
       # chronological (i.e. a !!timestamp value), but could also be, e.g,
       # alphabetical or just sequence-numbered. Any sortable type will do.
       'order_by': 'pub_date',
       # If present, lists will be paginated with this number of items per page.
       'num_per_page': 10,
       # If present, generate an RSS feed with the given properties.
       'feed': {
         # RSS feed title.
         'title': 'Example RSS Feed',
         # RSS feed link attribute.
         'link': 'http://www.example.com',
         # Description of the feed.
         'desc': 'An RSS Feed for Example.com: The Home of Example Content.',
         # Number of items to include in the feed (ordered by 'order_by' above).
         'num_items': 10,
         # Which item attribute to use as the RSS entry title.
         'item_title': 'title',
         # Which item attribute to use as the RSS entry description.
         'item_desc': 'summary'
       }
    }
  }

}
