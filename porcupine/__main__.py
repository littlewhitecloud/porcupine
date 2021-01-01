import argparse
import logging
import pathlib
import sys

# imports spread across multiple lines to keep sane line lengths and make it greppable
from porcupine import __version__ as porcupine_version
from porcupine import (_logs, _state, dirs, get_main_window, get_tab_manager, menubar, pluginloader, plugins, settings,
                       tabs)

log = logging.getLogger(__name__)


# see the --help action in argparse's source code
class _PrintPlugindirAction(argparse.Action):

    def __init__(   # type: ignore
            self, option_strings, dest=argparse.SUPPRESS,
            default=argparse.SUPPRESS, help=None):
        super().__init__(option_strings=option_strings, dest=dest,
                         default=default, nargs=0, help=help)

    def __call__(   # type: ignore
            self, parser, namespace, values, option_string=None):
        print("You can install plugins here:\n\n    %s\n" % plugins.__path__[0])
        parser.exit()


_EPILOG = r"""
Examples:
  %(prog)s                    # run Porcupine normally
  %(prog)s file1.py file2.js  # open the given files on startup
  %(prog)s -n Python          # create a new Python file
  %(prog)s --no-plugins       # understand the power of plugins
  %(prog)s -v                 # produce lots of output for debugging
"""


def main() -> None:
    # Arguments are parsed in two steps:
    #   1. only the arguments needed for importing plugins
    #   2. everything else
    #
    # Between those steps, plugins get a chance to add more command-line options.
    parser = argparse.ArgumentParser(
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,  # help in step 1 wouldn't show options added by plugins
    )
    parser.add_argument(
        '--version', action='version',
        version=("Porcupine %s" % porcupine_version),
        help="display the Porcupine version number and exit")
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help=("print all logging messages to stderr, only warnings and errors "
              "are printed by default (but all messages always go to a log "
              "file in %s as well)" % _logs.LOG_DIR))
    parser.add_argument(
        '--print-plugindir', action=_PrintPlugindirAction,
        help="find out where to install custom plugins")
    plugingroup = parser.add_argument_group("plugin loading options")
    plugingroup.add_argument(
        '--no-plugins', action='store_false', dest='use_plugins',
        help=("don't load any plugins, this is useful for "
              "understanding how much can be done with plugins"))
    plugingroup.add_argument(
        '--without-plugins', metavar='PLUGINS', default='',
        help=("don't load PLUGINS (see --print-plugindir), "
              "e.g. --without-plugins=highlight disables syntax highlighting, "
              "multiple plugin names can be given comma-separated"))

    args_parsed_in_first_step, junk = parser.parse_known_args()

    dirs.makedirs()
    _logs.setup(args_parsed_in_first_step.verbose)

    settings.init_enough_for_using_disabled_plugins_list()
    if args_parsed_in_first_step.use_plugins:
        if args_parsed_in_first_step.without_plugins:
            disable_list = args_parsed_in_first_step.without_plugins.split(',')
        else:
            disable_list = []
        pluginloader.import_plugins(disable_list)

        bad_disables = set(disable_list) - {info.name for info in pluginloader.plugin_infos}
        if bad_disables:
            one_of_them, *the_rest = bad_disables
            parser.error(f"--without-plugins: no plugin named {one_of_them!r}")

    parser.add_argument('--help', action='help', help="show this message")
    pluginloader.run_setup_argument_parser_functions(parser)
    parser.add_argument(
        'files', metavar='FILES', nargs=argparse.ZERO_OR_MORE,
        help="open these files when Porcupine starts, - means stdin")
    plugingroup.add_argument(
        '--shuffle-plugins', action='store_true',
        help=("respect setup_before and setup_after, but otherwise setup the "
              "plugins in a random order instead of sorting by name "
              "alphabetically, useful for making sure that your plugin's "
              "setup_before and setup_after define everything needed; usually "
              "plugins are not shuffled in order to make the UI consistent"))
    args = parser.parse_args()

    _state.init(args)
    settings.init_the_rest_after_initing_enough_for_using_disabled_plugins_list()
    menubar._init()

    pluginloader.run_setup_functions(args.shuffle_plugins)

    tabmanager = get_tab_manager()
    for path_string in args.files:
        if path_string == '-':
            # don't close stdin so it's possible to do this:
            #
            #   $ porcu - -
            #   bla bla bla
            #   ^D
            #   bla bla
            #   ^D
            tab = tabs.FileTab(tabmanager, content=sys.stdin.read())
        else:
            tab = tabs.FileTab.open_file(tabmanager, pathlib.Path(path_string))
        tabmanager.add_tab(tab)

    try:
        get_main_window().mainloop()
    finally:
        settings.save()
    log.info("exiting Porcupine successfully")


# python3 -m pocupine
if __name__ == '__main__':
    main()
