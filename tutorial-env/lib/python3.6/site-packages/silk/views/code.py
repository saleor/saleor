from silk.config import SilkyConfig

__author__ = 'mtford'


def _code(file_path, line_num, end_line_num=None):
    line_num = int(line_num)
    if not end_line_num:
        end_line_num = line_num
    end_line_num = int(end_line_num)
    actual_line = []
    lines = ''
    with open(file_path, 'r') as f:
        r = range(max(0, line_num - 10), line_num + 10)
        for i, line in enumerate(f):
            if i in r:
                lines += line
            if i + 1 in range(line_num, end_line_num + 1):
                actual_line.append(line)
    code = lines.split('\n')
    return actual_line, code


def _code_context(file_path, line_num, end_line_num=None, prefix=''):
    actual_line, code = _code(file_path, line_num, end_line_num)
    return {
        prefix + 'code': code,
        prefix + 'file_path': file_path,
        prefix + 'line_num': line_num,
        prefix + 'actual_line': actual_line
    }


def _code_context_from_request(request, end_line_num=None, prefix=''):
    file_path = request.GET.get('file_path')
    line_num = request.GET.get('line_num')
    result = {}
    if file_path is not None and line_num is not None:
        result = _code_context(file_path, line_num, end_line_num, prefix)
    return result


def _should_display_file_name(file_name):
    for ignored_file in SilkyConfig().SILKY_IGNORE_FILES:
        if ignored_file in file_name:
            return False
    return True
