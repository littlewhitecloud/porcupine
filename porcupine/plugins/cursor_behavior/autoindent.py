"""Indenting and dedenting automatically.

This must be ran *after* stripping the trailing whitespace because
otherwise pressing enter twice would strip all trailing whitespace from
the blank line above the cursor, and then on_enter() wouldn't do anything.
"""

import porcupine
from porcupine import tabs


def leading_whitespace(string):
    r"""Return leading whitespace characters. Ignores trailing '\n'.

    >>> leading_whitespace('\t \t lel')
    '\t \t '
    >>> leading_whitespace('  \n')
    '  '
    """
    count = len(string) - len(string.lstrip())
    return string[:count].rstrip('\n')


def after_enter(textwidget):
    """Indent or dedent the current line automatically if needed."""
    lineno = int(textwidget.index('insert').split('.')[0])
    prevline = textwidget.get('%d.0 - 1 line' % lineno, '%d.0' % lineno)
    textwidget.insert('insert', leading_whitespace(prevline))

    # we can't strip trailing whitespace before this because then
    # pressing enter twice would get rid of all indentation
    # TODO: make this language-specific instead of always using python stuff
    prevline = prevline.strip()
    if prevline.endswith((':', '(', '[', '{')):
        # start of a new block
        textwidget.indent('insert')
    elif (prevline in {'return', 'break', 'pass', 'continue'} or
          prevline.startswith(('return ', 'raise '))):
        # must be end of a block
        textwidget.dedent('insert')


def on_new_tab(event):
    tab = event.widget.tabs[-1]
    if isinstance(tab, tabs.FileTab):
        def bind_callback(event):
            tab.textwidget.after_idle(after_enter, tab.textwidget)

        tab.textwidget.bind('<Return>', bind_callback)


def setup():
    porcupine.get_tab_manager().bind('<<NewTab>>', on_new_tab, add=True)


if __name__ == '__main__':
    import doctest
    print(doctest.testmod())
