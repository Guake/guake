Please follow these steps before submitting a new Pull Request to Guake:

- rebase on latest HEAD
- describe your change in the pull request
- execute the code styling using:
  ```bash
  $ make style
  ```
- add a slug in release note using:
  ```bash
  $ make reno SLUG=<short_name_of_my_feature>
  ```
  and edit the created file in `releasenotes/notes/`.

  You can see how `reno` works using `pipenv run reno --help`.
