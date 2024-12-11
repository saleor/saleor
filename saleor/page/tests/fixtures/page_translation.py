import pytest

from ....tests.utils import dummy_editorjs
from ...models import PageTranslation


@pytest.fixture
def page_translation_fr(page):
    return PageTranslation.objects.create(
        language_code="fr",
        page=page,
        title="French page title",
        content=dummy_editorjs("French page content."),
    )
