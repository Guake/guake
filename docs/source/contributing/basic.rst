
Basic Details
=============

If you would like to contribute to the development of Guake, here are some general information.

Found a Bug?
------------

Before opening a new issue, please read the following:

- for **feature requests**, please use `FeatHub <https://feathub.com/Guake/guake>`_ ).
  This allow us to spot directly which are the most requested features.
- A `Bountysource page <https://www.bountysource.com/teams/guake>`_ also exists for
  requesting new features for Guake.
- before opening **a new bug**, please search for a similar one in the
  `GitHub Issues <https://github.com/Guake/guake/issues>`_ .


Submitting a Pull Request
-------------------------

Please follow these steps before submitting a new Pull Request to Guake:

- rebase on latest HEAD with ``git pull rebase upstream master``
- describe your change in the pull request
- execute the code styling, checks and unit tests using:
  ``$ make style check reno-lint test``
- add a slug in release note using ``$ make reno SLUG=<short_name_of_my_feature>``
  and edit the created file in `releasenotes/notes/`.

  You can see how `reno` works using `pipenv run reno --help`.
  Please use a generic slug (eg, for translation update, use `translation`)
