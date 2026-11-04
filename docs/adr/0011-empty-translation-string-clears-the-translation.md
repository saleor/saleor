# An empty translation string clears the translation

**Tags:** translations, graphql

Saving `""` as a translated value clears it. The API returns `null` for that field, the same as
when the field was never translated. All string fields of translation types are nullable, so this
works the same way for every translatable object.

Before, the behaviour depended on the type. Some fields were nullable and returned `""`, and some
were non-null and could only return `""`. A client couldn't tell an intentionally empty translation
from a missing one, so it had to guess whether to fall back to the original value. Now `null` always
means "no translation, use the original", and a client can fall back with `??`.

Making the non-null fields nullable is a breaking schema change. We accepted it so that all
translations behave the same.
