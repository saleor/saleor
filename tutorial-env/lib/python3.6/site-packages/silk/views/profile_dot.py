# std
import os
import json
import tempfile
import shutil
from contextlib import closing, contextmanager
# 3rd party
from six import StringIO
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.http import HttpResponse
from gprof2dot import DotWriter, PstatsParser, Theme
# silk
from silk.auth import login_possibly_required, permissions_possibly_required
from silk.models import Request


COLOR_MAP = Theme(
    mincolor=(0.18, 0.51, 0.53),
    maxcolor=(0.03, 0.49, 0.50),
    gamma=1.5,
    fontname='FiraSans',
    minfontsize=6.0,
    maxfontsize=6.0,
)


@contextmanager
def _temp_file_from_file_field(source):
    """
    Create a temp file containing data from a django file field.
    """
    source.open()
    with closing(source):
        try:
            with tempfile.NamedTemporaryFile(delete=False) as destination:
                shutil.copyfileobj(source, destination)
            yield destination.name
        finally:
            os.unlink(destination.name)


def _create_profile(source, get_filename=_temp_file_from_file_field):
    """
    Parse a profile from a django file field source.
    """
    with get_filename(source) as filename:
        return PstatsParser(filename).parse()


def _create_dot(profile, cutoff):
    """
    Create a dot file from pstats data stored in a django file field.
    """
    node_cutoff = cutoff / 100.0
    edge_cutoff = 0.1 / 100.0
    profile.prune(node_cutoff, edge_cutoff, False)

    with closing(StringIO()) as fp:
        DotWriter(fp).graph(profile, COLOR_MAP)
        return fp.getvalue()


class ProfileDotView(View):

    @method_decorator(login_possibly_required)
    @method_decorator(permissions_possibly_required)
    def get(self, request, request_id):
        silk_request = get_object_or_404(Request, pk=request_id, prof_file__isnull=False)
        cutoff = float(request.GET.get('cutoff', '') or 5)
        profile = _create_profile(silk_request.prof_file)
        result = dict(dot=_create_dot(profile, cutoff))
        return HttpResponse(json.dumps(result).encode('utf-8'), content_type='application/json')
