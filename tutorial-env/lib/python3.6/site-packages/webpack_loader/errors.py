from django.core.checks import Error


BAD_CONFIG_ERROR = Error(
    'Error while parsing WEBPACK_LOADER configuration',
    hint='Is WEBPACK_LOADER config valid?',
    obj='django.conf.settings.WEBPACK_LOADER',
    id='django-webpack-loader.E001',
)
