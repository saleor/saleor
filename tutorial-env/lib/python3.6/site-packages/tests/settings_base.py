import os

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(PROJECT_DIR, 'media')
SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "versatileimagefield",
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

MIDDLEWARE = MIDDLEWARE_CLASSES

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'versatileimagefield_testing_cache',
    }
}

MEDIA_URL = '/media/'
STATIC_URL = '/static/'

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    'test_set': (
        ('test_thumb', 'thumbnail__100x100'),
        ('test_crop', 'crop__100x100'),
        ('test_invert', 'filters__invert__url'),
        ('test_invert_thumb', 'filters__invert__thumbnail__100x100'),
        ('test_invert_crop', 'filters__invert__crop__100x100'),
    ),
    'invalid_size_key': (
        ('test', 'thumbnail'),
    ),
    'invalid_set': ('test_thumb', 'thumbnail__100x100')
}

ROOT_URLCONF = 'tests.urls'
DEBUG = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(PROJECT_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
