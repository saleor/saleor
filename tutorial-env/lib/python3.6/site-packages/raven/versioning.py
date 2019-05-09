from __future__ import absolute_import

import os.path

from raven.utils.compat import text_type
from .exceptions import InvalidGitRepository

__all__ = ('fetch_git_sha', 'fetch_package_version')


def fetch_git_sha(path, head=None):
    """
    >>> fetch_git_sha(os.path.dirname(__file__))
    """
    if not head:
        head_path = os.path.join(path, '.git', 'HEAD')
        if not os.path.exists(head_path):
            raise InvalidGitRepository(
                'Cannot identify HEAD for git repository at %s' % (path,))

        with open(head_path, 'r') as fp:
            head = text_type(fp.read()).strip()

        if head.startswith('ref: '):
            head = head[5:]
            revision_file = os.path.join(
                path, '.git', *head.split('/')
            )
        else:
            return head
    else:
        revision_file = os.path.join(path, '.git', 'refs', 'heads', head)

    if not os.path.exists(revision_file):
        if not os.path.exists(os.path.join(path, '.git')):
            raise InvalidGitRepository(
                '%s does not seem to be the root of a git repository' % (path,))

        # Check for our .git/packed-refs' file since a `git gc` may have run
        # https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery
        packed_file = os.path.join(path, '.git', 'packed-refs')
        if os.path.exists(packed_file):
            with open(packed_file) as fh:
                for line in fh:
                    line = line.rstrip()
                    if line and line[:1] not in ('#', '^'):
                        try:
                            revision, ref = line.split(' ', 1)
                        except ValueError:
                            continue
                        if ref == head:
                            return text_type(revision)

        raise InvalidGitRepository(
            'Unable to find ref to head "%s" in repository' % (head,))

    with open(revision_file) as fh:
        return text_type(fh.read()).strip()


def fetch_package_version(dist_name):
    """
    >>> fetch_package_version('sentry')
    """
    try:
        # Importing pkg_resources can be slow, so only import it
        # if we need it.
        import pkg_resources
    except ImportError:
        # pkg_resource is not available on Google App Engine
        raise NotImplementedError('pkg_resources is not available '
                                  'on this Python install')
    dist = pkg_resources.get_distribution(dist_name)
    return dist.version
