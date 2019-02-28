
def resolve_translation(instance, info, language_code):
    """Gets translation object from instance based on language code."""
    return instance.translations.filter(language_code=language_code).first()
