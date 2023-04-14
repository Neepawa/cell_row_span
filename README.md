Table Cell and Row Span
=======================

NOTE: This is a fork of an excellent idea implemented by @Neepawa, however
the upstream seems to be abandoned for a while, so I collected different
patches across all forks and also updated the extension to work with the
latest version of [Python-Markdown][markdown].  I plan to maintain this
version (and push changes to upstream) as long as I am running my personal
blog on [Pelican][pelican], which heavily relies on Python-Markdown.

Summary
-------

A Python-Markdown extension to add the `colspan` and `rowspan` support for rows
and cells in tables.

Syntax
------

**Example:**

~~~ text
| Column 1                | Col 2 | Big row span   |
|:-----------------------:|-------| -------------- |
| r1_c1 spans two cols           || One large cell |
| r2_c1 spans two rows    | r2_c2 |                |
|_^                      _| r3_c2 |                |
|    ______ &#20;         | r4_c2 |_              _|
~~~

The example renders as:

~~~ text
    .--------------------------------------------------.
    |        Column 1         | Col 2 |  Big row span  |
    |---------------------------------+----------------|
    |      r1_c1 spans two cols       |                |
    |---------------------------------|                |
    |  r2_c1 spans two rows   | r2_c2 |                |
    |                         |-------| One large cell |
    |                         | r3_c2 |                |
    |-------------------------+-------|                |
    |          ____           | r4_c2 |                |
    `--------------------------------------------------'
~~~

To span cells across multiple columns, end them with two or more consecutive
vertical bars. Cells to the left will be merged together, as many cells are
there are bars. In the example above, there are two bars at the end of cell
2 on row 1, so the two cells to the left of it (numbers 1 and 2) are merged.

To span cells across rows, fill the cell on the last row with at least two
underscores, one at the start and the other at the end of its content, and no
other characters than spaces, underscores, `^` or `=`. This is referred to as
the *marker.* The cell with the marker and all the empty cells above it to the
first non-empty cell will be made into a single cell, with the content of the
non-empty cell. See column 3 ("Big row span") in the example.

By default the contents are vertically aligned in the middle of the cell. To
align to the top, include at least one `^` character in the marker between the
two underscores; for example, `|_^^^_|` or simply `|_^   _|`. See row 2 in
column 1 of the example, which is merged with row 3 and aligned at the top. To
align to the bottom, use at least one `=` character between the underscores;
for example, `|_ = _|`.  Including both `^` and `=` in a marker raises a
`ValueError` exception.

Note: If this extension finds a cell with at least two underscores and no other
characters other than spaces, `^` or `=`, it assumes it's a row span marker and
attempts to process it. If you need a cell that looks like a marker (generally
one with only underscores in it), add the text `&#20;` as well---this extension
won't process it as a row span marker and Markdown will change the `&#20;` to a
space.

Bug in Markdown 2.6
-------------------

Python Markdown 2.6 does not process the following table correctly:

~~~ text
| Column 1 | Column 2 | Column 3 | Column 4 |
| -------- | -------- | -------- | -------- |
| r1,c1    | r1,c2    | r1,c3    | r1,c4    |
| r2,c1              || r2,c3    | r2,c4    |
~~~

The table should be rendered as follows:

~~~ text
    .-------------------------------------------.
    | Column 1 | Column 2 | Column 3 | Column 4 |
    |----------+----------+----------+----------|
    | r1,c1    | r1,c2    | r1,c3    | r1,c4    |
    |----------+----------+----------+----------|
    | r2,c1               | r2,c3    | r2,c4    |
    `-------------------------------------------'
~~~

Instead it comes out as:

~~~ text
    .-------------------------------------------.
    | Column 1 | Column 2 | Column 3 | Column 4 |
    |----------+----------+----------+----------|
    | r1,c1    | r1,c2    | r1,c3    | r1,c4    |
    |----------+----------+----------+----------|
    | r2,c1               | r2,c4    |          |
    `-------------------------------------------'
~~~

The bug is in the *tables* extension, not this one. If you're having problems
getting a table with column spans to work correctly in Markdown 2.6, try
replacing `||` with `|~~|`, as follows:

~~~ text
| Column 1 | Column 2 | Column 3 | Column 4 |
| -------- | -------- | -------- | -------- |
| r1,c1    | r1,c2    | r1,c3    | r1,c4    |
| r2,c1            |~~| r2,c3    | r2,c4    |
~~~

The table extension processes the above correctly, and this extension recognizes
a cell containing only `~~` as an empty cell. (I chose `~~` because I can't think
of a reason anyone would use that in a cell.) If you want to use something
different, change `~~` to another value in the following line in the code:

    RE_empty_cell = re.compile(r'\s*(~~)?\s*$')

Keep in mind that many characters have special meaning in regular expressions.
If you use any of the following characters in the expression, precede them with
a backslash ("\\") to avoid problems:

~~~ text
. + * | ? $ ( ) [ ] { }
~~~

Usage
-----

See [Extensions][extensions] for general extension usage. Use `cell_row_span`
as the name of the extension. You must include the `tables` extension *before*
this one, or this extension will not be run.

This extension does not accept any special configuration options.

See <https://python-markdown.github.io/extensions/tables/> for documentation on
the **tables** extension.

This extension works with Python Markdown versions 2.6 and 3 under Python 2
and Python 3.

License: [BSD](http://www.opensource.org/licenses/bsd-license.php)

[extensions]: https://python-markdown.github.io/extensions/
[markdown]: https://github.com/Python-Markdown/markdown
[pelican]: https://github.com/getpelican/pelican
