"""benchmarking through py.test"""

from __future__ import print_function, division

import py
from py.__.test.item import Item
from py.__.test.terminal.terminal import TerminalSession

from math import ceil as _ceil, floor as _floor, log10
import timeit

from inspect import getsource

from sympy.core.compatibility import exec_, range


# from IPython.Magic.magic_timeit
units = ["s", "ms", "us", "ns"]
scaling = [1, 1e3, 1e6, 1e9]

unitn = dict((s, i) for i, s in enumerate(units))

precision = 3


# like py.test Directory but scan for 'bench_<smth>.py'
class Directory(py.test.collect.Directory):

    def filefilter(self, path):
        b = path.purebasename
        ext = path.ext
        return b.startswith('bench_') and ext == '.py'


# like py.test Module but scane for 'bench_<smth>' and 'timeit_<smth>'
class Module(py.test.collect.Module):

    def funcnamefilter(self, name):
        return name.startswith('bench_') or name.startswith('timeit_')


# Function level benchmarking driver
class Timer(timeit.Timer):

    def __init__(self, stmt, setup='pass', timer=timeit.default_timer, globals=globals()):
        # copy of timeit.Timer.__init__
        # similarity index 95%
        self.timer = timer
        stmt = timeit.reindent(stmt, 8)
        setup = timeit.reindent(setup, 4)
        src = timeit.template % {'stmt': stmt, 'setup': setup}
        self.src = src  # Save for traceback display
        code = compile(src, timeit.dummy_src_name, "exec")
        ns = {}
        #exec code in globals(), ns      -- original timeit code
        exec_(code, globals, ns)  # -- we use caller-provided globals instead
        self.inner = ns["inner"]


class Function(py.__.test.item.Function):

    def __init__(self, *args, **kw):
        super(Function, self).__init__(*args, **kw)
        self.benchtime = None
        self.benchtitle = None

    def execute(self, target, *args):
        # get func source without first 'def func(...):' line
        src = getsource(target)
        src = '\n'.join( src.splitlines()[1:] )

        # extract benchmark title
        if target.func_doc is not None:
            self.benchtitle = target.func_doc
        else:
            self.benchtitle = src.splitlines()[0].strip()

        # XXX we ignore args
        timer = Timer(src, globals=target.func_globals)

        if self.name.startswith('timeit_'):
            # from IPython.Magic.magic_timeit
            repeat = 3
            number = 1
            for i in range(1, 10):
                t = timer.timeit(number)

                if t >= 0.2:
                    number *= (0.2 / t)
                    number = int(_ceil(number))
                    break

                if t <= 0.02:
                    # we are not close enough to that 0.2s
                    number *= 10

                else:
                    # since we are very close to be > 0.2s we'd better adjust number
                    # so that timing time is not too high
                    number *= (0.2 / t)
                    number = int(_ceil(number))
                    break

            self.benchtime = min(timer.repeat(repeat, number)) / number

        # 'bench_<smth>'
        else:
            self.benchtime = timer.timeit(1)


class BenchSession(TerminalSession):

    def header(self, colitems):
        super(BenchSession, self).header(colitems)

    def footer(self, colitems):
        super(BenchSession, self).footer(colitems)

        self.out.write('\n')
        self.print_bench_results()

    def print_bench_results(self):
        self.out.write('==============================\n')
        self.out.write(' *** BENCHMARKING RESULTS *** \n')
        self.out.write('==============================\n')
        self.out.write('\n')

        # benchname, time, benchtitle
        results = []

        for item, outcome in self._memo:
            if isinstance(item, Item):

                best = item.benchtime

                if best is None:
                    # skipped or failed benchmarks
                    tstr = '---'

                else:
                    # from IPython.Magic.magic_timeit
                    if best > 0.0:
                        order = min(-int(_floor(log10(best)) // 3), 3)
                    else:
                        order = 3

                    tstr = "%.*g %s" % (
                        precision, best * scaling[order], units[order])

                results.append( [item.name, tstr, item.benchtitle] )

        # dot/unit align second column
        # FIXME simpler? this is crappy -- shame on me...
        wm = [0]*len(units)
        we = [0]*len(units)

        for s in results:
            tstr = s[1]
            n, u = tstr.split()

            # unit n
            un = unitn[u]

            try:
                m, e = n.split('.')
            except ValueError:
                m, e = n, ''

            wm[un] = max(len(m), wm[un])
            we[un] = max(len(e), we[un])

        for s in results:
            tstr = s[1]
            n, u = tstr.split()

            un = unitn[u]

            try:
                m, e = n.split('.')
            except ValueError:
                m, e = n, ''

            m = m.rjust(wm[un])
            e = e.ljust(we[un])

            if e.strip():
                n = '.'.join((m, e))
            else:
                n = ' '.join((m, e))

            # let's put the number into the right place
            txt = ''
            for i in range(len(units)):
                if i == un:
                    txt += n
                else:
                    txt += ' '*(wm[i] + we[i] + 1)

            s[1] = '%s %s' % (txt, u)

        # align all columns besides the last one
        for i in range(2):
            w = max(len(s[i]) for s in results)

            for s in results:
                s[i] = s[i].ljust(w)

        # show results
        for s in results:
            self.out.write('%s  |  %s  |  %s\n' % tuple(s))


def main(args=None):
    # hook our Directory/Module/Function as defaults
    from py.__.test import defaultconftest

    defaultconftest.Directory = Directory
    defaultconftest.Module = Module
    defaultconftest.Function = Function

    # hook BenchSession as py.test session
    config = py.test.config
    config._getsessionclass = lambda: BenchSession

    py.test.cmdline.main(args)
