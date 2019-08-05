"""Shell command line utilities for tests"""

import sys
from io import StringIO


def run_main(the_main_function, arguments):
    """Emulate exec call for command line tool main() functions.

    This function runs given function and captures any stdout/stderr
    output.

    Usage::

        import scriptmodule
        (returncode, stdout, stderr) = run_command(
            scriptmodule.main, options, arguments)

    Parameters:

        :the_main_function: Function reference to execute
        :options: Options to pass ass optparse.parse_options() options.
        :args: Options to pass ass optparse.parse_options() argumens.


    """

    stdout_original = sys.stdout
    stderr_original = sys.stderr
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()

    sys.stdout = stdout_buffer
    sys.stderr = stderr_buffer

    returnstatus = -1

    try:
        returnstatus = the_main_function(arguments)
    finally:
        stdout = stdout_buffer.getvalue()
        stderr = stderr_buffer.getvalue()
        sys.stdout = stdout_original
        sys.stderr = stderr_original

    return (returnstatus, stdout, stderr)
