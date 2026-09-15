# Saleor version numbers do not follow Semantic Versioning

**Tags:** versioning

Saleor uses a three-component version number such as `3.24.0`, but the components
do not carry the guarantees defined by Semantic Versioning. In particular, a
minor release may contain backward-incompatible changes, while a patch release
on an active release line may add functionality or require schema migrations.

The major component identifies a broad release generation; it is not the only
component in which backward-incompatible changes may appear. Therefore, the
version-number difference alone does not describe an upgrade's compatibility or
scope.

Before upgrading, users must consult `CHANGELOG.md` and the applicable upgrade
notes instead of inferring compatibility from the version number.
