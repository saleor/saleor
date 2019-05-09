from __future__ import absolute_import, unicode_literals

import time

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from debug_toolbar.panels import Panel

try:
    import resource  # Not available on Win32 systems
except ImportError:
    resource = None


class TimerPanel(Panel):
    """
    Panel that displays the time a response took in milliseconds.
    """

    def nav_subtitle(self):
        stats = self.get_stats()
        if hasattr(self, "_start_rusage"):
            utime = self._end_rusage.ru_utime - self._start_rusage.ru_utime
            stime = self._end_rusage.ru_stime - self._start_rusage.ru_stime
            return _("CPU: %(cum)0.2fms (%(total)0.2fms)") % {
                "cum": (utime + stime) * 1000.0,
                "total": stats["total_time"],
            }
        elif "total_time" in stats:
            return _("Total: %0.2fms") % stats["total_time"]
        else:
            return ""

    has_content = resource is not None

    title = _("Time")

    template = "debug_toolbar/panels/timer.html"

    @property
    def content(self):
        stats = self.get_stats()
        rows = (
            (_("User CPU time"), _("%(utime)0.3f msec") % stats),
            (_("System CPU time"), _("%(stime)0.3f msec") % stats),
            (_("Total CPU time"), _("%(total)0.3f msec") % stats),
            (_("Elapsed time"), _("%(total_time)0.3f msec") % stats),
            (
                _("Context switches"),
                _("%(vcsw)d voluntary, %(ivcsw)d involuntary") % stats,
            ),
        )
        return render_to_string(self.template, {"rows": rows})

    def process_request(self, request):
        self._start_time = time.time()
        if self.has_content:
            self._start_rusage = resource.getrusage(resource.RUSAGE_SELF)

    def generate_stats(self, request, response):
        stats = {}
        if hasattr(self, "_start_time"):
            stats["total_time"] = (time.time() - self._start_time) * 1000
        if hasattr(self, "_start_rusage"):
            self._end_rusage = resource.getrusage(resource.RUSAGE_SELF)
            stats["utime"] = 1000 * self._elapsed_ru("ru_utime")
            stats["stime"] = 1000 * self._elapsed_ru("ru_stime")
            stats["total"] = stats["utime"] + stats["stime"]
            stats["vcsw"] = self._elapsed_ru("ru_nvcsw")
            stats["ivcsw"] = self._elapsed_ru("ru_nivcsw")
            stats["minflt"] = self._elapsed_ru("ru_minflt")
            stats["majflt"] = self._elapsed_ru("ru_majflt")
            # these are documented as not meaningful under Linux.  If you're
            # running BSD feel free to enable them, and add any others that I
            # hadn't gotten to before I noticed that I was getting nothing but
            # zeroes and that the docs agreed. :-(
            #
            #        stats['blkin'] = self._elapsed_ru('ru_inblock')
            #        stats['blkout'] = self._elapsed_ru('ru_oublock')
            #        stats['swap'] = self._elapsed_ru('ru_nswap')
            #        stats['rss'] = self._end_rusage.ru_maxrss
            #        stats['srss'] = self._end_rusage.ru_ixrss
            #        stats['urss'] = self._end_rusage.ru_idrss
            #        stats['usrss'] = self._end_rusage.ru_isrss

        self.record_stats(stats)

    def generate_server_timing(self, request, response):
        stats = self.get_stats()

        self.record_server_timing("utime", "User CPU time", stats.get("utime", 0))
        self.record_server_timing("stime", "System CPU time", stats.get("stime", 0))
        self.record_server_timing("total", "Total CPU time", stats.get("total", 0))
        self.record_server_timing(
            "total_time", "Elapsed time", stats.get("total_time", 0)
        )

    def _elapsed_ru(self, name):
        return getattr(self._end_rusage, name) - getattr(self._start_rusage, name)
