=====================
Release Procedure
=====================

- Ensure ``requirements.txt`` is up to date with the Pipfile.lock, or we will have
  ``dev0`` version generated
- Merge all translation from Weblate
- Generate the release notes, and updates NEWS.rst with the upcoming release.
- Ensure this pull request build.
- Merge
- Tag with the same version
