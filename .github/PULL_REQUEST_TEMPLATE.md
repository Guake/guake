Please follow these steps before submitting a new Pull Request to Guake:

- rebase on latest HEAD:

  ```bash
  $ git pull --rebase upstream master
  ```

- hack your change

- to execute the code styling, checks and unit tests:

  ```bash
  $ make style check reno-lint test
  ```

- describe your change in a slug file for automatic release note
  generation, using:

  ```bash
  $ make reno SLUG=<short_name_of_my_feature>
  ```

  and edit the created file in `releasenotes/notes/`.
  You can see how `reno` works using `pipenv run reno --help`.

  Please use a generic slug (eg, for translation update,
  use `translation`, for bugfix use `bugfix`,...)

- create new commit message

  ```bash
  $ <hack the code>
  $ git commit --all
  ```

- If your change is related to a GitHub issue, you can add a reference
  using `#123` where 123 is the ID of the issue.
  You can use `closes #123` to have GitHub automatically close the issue
  when your contribution get merged

- Semantic commit is supported (and recommended). Add one of the following
  line in your commit messages:

  ```
  # For a bug fix, uses:
  sem-ver: bugfix

  # For a new feature, uses:
  sem-ver: feature

  # Please do not use the 'breaking change' syntax (`sem-ver: api-break`),
  # it is reserved for really big reworks
  ```
