from six import text_type
import re


_pattern = re.compile(' +')


def parse_profile(output):
    """
    Parse the output of cProfile to a list of tuples.
    """
    if isinstance(output, text_type):
        output = output.split('\n')
    for i, line in enumerate(output):
        # ignore n function calls, total time and ordered by and empty lines
        line = line.strip()
        if i > 3 and line:
            columns = _pattern.split(line)[0:]
            function = ' '.join(columns[5:])
            columns = columns[:5] + [function]
            yield columns
