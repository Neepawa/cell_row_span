"""
Table Cell and Row Span extension for Python Markdown
=====================================================

Adds spanning for rows and cells in tables.

**Example:**

    | Column 1                | Col 2 | Big row span   |
    |:-----------------------:|-------| -------------- |
    | r1_c1 spans two cols           || One large cell |
    | r2_c1 spans two rows    | r2_c2 |                |
    |_^                      _| r3_c2 |                |
    |    ______ &#20;         | r4_c2 |_              _|

The example renders as:

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

To span cells across multiple columns, end them with two or more consecutive
vertical bars. Cells to the left will be merged together, as many cells are
there are bars. In the example above, there are two bars at the end of cell
2 on row 1, so the two cells to the left of it (numbers 1 and 2) are merged.

To span cells across rows, fill the cell on the last row with at least two
underscores, one at the start and the other at the end of its content, and no
other characters than spaces, underscores, '^' or '='. This is referred to as
the *marker.* The cell with the marker and all the empty cells above it to the
first non-empty cell will be made into a single cell, with the content of the
non-empty cell. See column 3 ("Big row span") in the example.

By default the contents are vertically aligned in the middle of the cell. To
align to the top, include at least one '^' character in the marker between the
two underscores; for example, '|_^^^_|' or simply '|_^   _|'. See row 2 in
column 1 of the example, which is merged with row 3 and aligned at the top. To
align to the bottom, use at least one '=' character between the underscores;
for example, '|_ = _|'.  Including both '^' and '=' in a marker raises a
'ValueError' exception.

Note: If this extension finds a cell with at least two underscores and no other
characters other than spaces, '^' or '=', it assumes it's a row span marker and
attempts to process it. If you need a cell that looks like a marker (generally
one with only underscores in it), add the text '&#20;' as well---this extension
won't process it as a row span marker and Markdown will change the '&#20;' to a
space.

Bug in Markdown 2.6: Python Markdown 2.6 does not process the following table
correctly:

    | Column 1 | Column 2 | Column 3 | Column 4 |
    | -------- | -------- | -------- | -------- |
    | r1,c1    | r1,c2    | r1,c3    | r1,c4    |
    | r2,c1              || r2,c3    | r2,c4    |

The table should be rendered as follows:

        .-------------------------------------------.
        | Column 1 | Column 2 | Column 3 | Column 4 |
        |----------+----------+----------+----------|
        | r1,c1    | r1,c2    | r1,c3    | r1,c4    |
        |----------+----------+----------+----------|
        | r2,c1               | r2,c3    | r2,c4    |
        `-------------------------------------------'

Instead it comes out as:

        .-------------------------------------------.
        | Column 1 | Column 2 | Column 3 | Column 4 |
        |----------+----------+----------+----------|
        | r1,c1    | r1,c2    | r1,c3    | r1,c4    |
        |----------+----------+----------+----------|
        | r2,c1               | r2,c4    |          |
        `-------------------------------------------'

The bug is in the *tables* extension, not this one. If you're having problems
getting a table with column spans to work correctly in Markdown 2.6, try
replacing '||' with '|~~|', as follows:

    | Column 1 | Column 2 | Column 3 | Column 4 |
    | -------- | -------- | -------- | -------- |
    | r1,c1    | r1,c2    | r1,c3    | r1,c4    |
    | r2,c1            |~~| r2,c3    | r2,c4    |

The table extension processes the above correctly, and this extension recognizes
a cell containing only '~~' as an empty cell. (I chose '~~' because I can't think
of a reason anyone would use that in a cell.) If you want to use something
different, change '~~' to another value in the following line in the code:

    RE_empty_cell = re.compile(r'\s*(~~)?\s*$')

Keep in mind that many characters have special meaning in regular expressions.
If you use any of the following characters in the expression, preceed them with
a backslash ("\\") to avoid problems:

    . + * | ? $ ( ) [ ] { }

Usage: See Extensions for general extension usage. Use 'cell_row_span' as the
name of the extension. You must include the 'tables' extension *before* this
one, or this extension will not be run.

This extension does not accept any special configuration options.

See <https://python-markdown.github.io/extensions/tables/> for documentation on
the **tables** extension.

This extension works with Python Markdown versions 2.6 and 3 under Python 2
and Python 3.

License: [BSD](http://www.opensource.org/licenses/bsd-license.php)

"""

from markdown.extensions import Extension
from markdown.blockprocessors import BlockProcessor
from markdown.treeprocessors import Treeprocessor
from markdown.util import etree
import re


class CellRowSpanExtension(Extension):
    """ Table Cell and Row Span extension """

    # Table blocks found by the block processor. Because we need to share the
    # list between the block and the tree processors, we make it a property of
    # the extension itself.
    table_blocks = []

    def extendMarkdown(self, md, md_globals):
        """ Add our block and tree processors """
        if 'table' in md.parser.blockprocessors:
           md.parser.blockprocessors.add('cell_row_span',
             CellRowSpanBlockProcessor(self, md.parser), '<table')
           md.treeprocessors.add('cell_row_span',
             CellRowSpanTreeProcessor(self), '<inline')


class CellRowSpanBlockProcessor(BlockProcessor):
    """ Save the current block if it's a table """
    table_blockprocessor = None

    def __init__(self, extension_obj, md_parser):
        self.table_blocks = extension_obj.table_blocks
        self.table_blockprocessor = md_parser.blockprocessors['table']
        super(CellRowSpanBlockProcessor, self).__init__(md_parser)

    def test(self, parent, block):
        """ Use the 'table' BlockProcessor's test method to determine if this a table block """
        return self.table_blockprocessor.test(parent, block)

    def run(self, parent, blocks):
        """ Add the table block's source to our list """
        self.table_blocks.append(blocks[0])
        return False    # Tell the BlockProcessor we didn't process the block


class CellRowSpanTreeProcessor(Treeprocessor):
    """ Add cell and row spans to table as needed """

    RE_adjacent_bars = re.compile(r'\|(~~)?\|')
    RE_remove_lead_pipe = re.compile(r'^ *\|')  # ... Colonel Mustard in the Library? ;)
    RE_row_span_marker = re.compile(r'^_[_^= ]*_$')
    RE_valign_top = re.compile(r'\^')
    RE_valign_bottom = re.compile(r'=')
    RE_empty_cell = re.compile(r'\s*(~~)?\s*$')

    def __init__(self, extension_obj):
        self.table_blocks = extension_obj.table_blocks
        super(CellRowSpanTreeProcessor, self).__init__()

    def _update_colspan_attrib(self, text, t_index, tr_index, tr, td_remove):
        """ Update 'colspan' attributes in 'td' entries """
        text = self.RE_remove_lead_pipe.sub('', text)   # Remove leading '|' from text
        td_index = 0
        td_last_active_index = 0

        for c in text.split('|'):
            if len(c) == 0 or c == '~~':
                try:
                    td = tr[td_last_active_index]           #  Update 'colspan' on previous cell
                except IndexError:
                    row_content = ''
                    for i in range(len(tr)):
                        x = tr[i].text
                        row_content += "  Cell %i: %s\n" % (i+1, x if x else 'Empty')
                    raise IndexError(
                        'Cannot merge cell beyond end of row '
                        "(one too many '|' characters in row?)\n"
                        'Check row %i of table %i in your document. Row contents:\n%s' % (
                            tr_index+1, t_index, row_content
                        )
                    )
                if td_index < len(tr):
                    span = 1
                    if 'colspan' in td.keys():
                        span = int(td.get('colspan'))
                    td.set('colspan', str(span+1))
                    td_remove.append( (tr, tr[td_index]) )
            else:
                td_last_active_index = td_index
            td_index += 1

    def _update_rowspan_attrib(self, tbody, tr_index, td_index, td_remove):
        """ Update 'rowspan' attributes in 'td' entries """
        # Look for '^' (vertical align top) or '=' (bottom) in the marker
        marker = tbody[tr_index][td_index].text
        v_align = 'middle'
        if self.RE_valign_top.search(marker):
            v_align = 'top'
        if self.RE_valign_bottom.search(marker):
            if v_align == 'top':
                raise ValueError(
                    'Cannot use both ^ (top) and = (bottom) codes in a row span '
                    'marker\nCheck row %i, column %i in table %i in your '
                    'document' % (tr_index+1, td_index+1, self.table_count)
                )
            v_align='bottom'

        # Starting from the current row, go up the rows and delete columns
        # until we hit a non-empty column (or the start of the table)
        for row_num in reversed(range(tr_index+1)):
            td = tbody[row_num][td_index]
            if row_num == tr_index or self.RE_empty_cell.match(td.text):
                td_remove.append( (tbody[row_num], td) )
            else:
                break

        # Update the colspan and valign attributes on the row
        td = tbody[row_num][td_index] if row_num >=0 else tbody[0][td_index]
        td.set('rowspan', str(tr_index-row_num+1))


    def run(self, root):
        # Process all the tables in the ElementTree
        t_index = 0
        for table in root.findall('.//table'):
            # Retrieve the block saved by the BlockProcessor
            rows = self.table_blocks[t_index].split('\n')
            t_index += 1

            # Scan the original table text for adjacent columns and spanned rows
            tbody = table.find('tbody')
            td_remove = []  # List of td objects to be removed
            tr_index = 0
            for tr in tbody:
                # Check for adjacent columns
                if tr_index + 2 in rows and self.RE_adjacent_bars.search(rows[tr_index+2]):
                    self._update_colspan_attrib(rows[tr_index+2], t_index, tr_index, tr, td_remove)
                # Check for spanned rows
                td_index = 0
                for td in tr:
                    if self.RE_row_span_marker.match(td.text):
                        self._update_rowspan_attrib(tbody, tr_index, td_index, td_remove)
                    td_index += 1
                tr_index += 1

            # Remove unneeded td elements
            for tr, td in td_remove:
                if td in tr:
                    tr.remove(td)

def makeExtension(*args, **kwargs):
    return CellRowSpanExtension(*args, **kwargs)
