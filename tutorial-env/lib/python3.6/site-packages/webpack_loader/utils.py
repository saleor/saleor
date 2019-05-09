from django.conf import settings

from .loader import WebpackLoader


_loaders = {}


def get_loader(config_name):
    if config_name not in _loaders:
        _loaders[config_name] = WebpackLoader(config_name)
    return _loaders[config_name]


def _filter_by_extension(bundle, extension):
    '''Return only files with the given extension'''
    for chunk in bundle:
        if chunk['name'].endswith('.{0}'.format(extension)):
            yield chunk


def _get_bundle(bundle_name, extension, config):
    bundle = get_loader(config).get_bundle(bundle_name)
    if extension:
        bundle = _filter_by_extension(bundle, extension)
    return bundle


def get_files(bundle_name, extension=None, config='DEFAULT'):
    '''Returns list of chunks from named bundle'''
    return list(_get_bundle(bundle_name, extension, config))


def get_as_tags(bundle_name, extension=None, config='DEFAULT', attrs=''):
    '''
    Get a list of formatted <script> & <link> tags for the assets in the
    named bundle.

    :param bundle_name: The name of the bundle
    :param extension: (optional) filter by extension, eg. 'js' or 'css'
    :param config: (optional) the name of the configuration
    :return: a list of formatted tags as strings
    '''

    bundle = _get_bundle(bundle_name, extension, config)
    tags = []
    for chunk in bundle:
        if chunk['name'].endswith(('.js', '.js.gz')):
            tags.append((
                '<script type="text/javascript" src="{0}" {1}></script>'
            ).format(chunk['url'], attrs))
        elif chunk['name'].endswith(('.css', '.css.gz')):
            tags.append((
                '<link type="text/css" href="{0}" rel="stylesheet" {1}/>'
            ).format(chunk['url'], attrs))
    return tags


def get_static(asset_name, config='DEFAULT'):
    '''
    Equivalent to Django's 'static' look up but for webpack assets.

    :param asset_name: the name of the asset
    :param config: (optional) the name of the configuration
    :return: path to webpack asset as a string
    '''
    return "{0}{1}".format(
        get_loader(config).get_assets().get(
            'publicPath', getattr(settings, 'STATIC_URL')
        ),
        asset_name
    )
