---
title: Contributing
---

We welcome all contributions to Saleor, including issues, new features, docs, discussions, and more. Read the following document to learn more about the process of contributing.

## Issues

Use [Github Issues](https://github.com/mirumee/saleor/issues) to report a bug or a problem that you found in Saleor. Use the "Bug report" issue template to provide information that will help us confirm the bug, such as steps to reproduce, expected behavior, Saleor version, and any additional context. When our team confirms a bug, it will be added to the internal backlog and picked up as soon as possible. When willing to fix a bug, let us know in the issue comment, and we will try to assist you on the way.

## New features
When willing to propose or add a new feature, we encourage you first to open a [discussion](https://github.com/mirumee/saleor/discussions) or an [issue](https://github.com/mirumee/saleor/issues) (using "Feature request" template) to discuss it with the core team. This process helps us decide if a feature is suitable for Saleor or design it before any implementation starts.

Before merging, any new pull requests submitted to Saleor have to be reviewed and approved by the core team. We review pull requests daily, but if a pull request requires more time or feedback from the team, it will be marked as "queued for review".

## Translations

All translations are contributed by the community. To aid with translation, visit our [Transifex project](https://www.transifex.com/mirumee/saleor-1/).

## Managing dependencies

### Poetry

To guarantee repeatable installations, all project dependencies are managed using [Poetry](https://poetry.eustace.io/). The project’s direct dependencies are listed in `pyproject.toml`.
Running `poetry lock` generates `poetry.lock` which has all versions pinned.

You can install Poetry by using `pip install --pre poetry` or by following the official installation guide [here](https://github.com/sdispater/poetry#installation).
We recommend using at least version `1.0.0b` as it contains many fixes and features that Saleor relies on.

*Tip:* We recommend that you use this workflow and keep `pyproject.toml` as well as `poetry.lock` under version control to make sure all computers and environments run exactly the same code.

### Other tools

For compatibility, Saleor also provides `requirements.txt` and `requirements_dev.txt`.

These files should be updated by running `poetry export --without-hashes -f requirements.txt -o requirements.txt` and `poetry export --without-hashes -f requirements.txt -o requirements_dev.txt --dev`, respectively.

## Coding style

Saleor uses various tools to maintain a common coding style and help with development.
To install all the development tools, run the following commands:

```shell
python -m pip install -r requirements_dev.txt
```

or use `poetry`:

```shell
poetry install
```

Saleor uses the [pre-commit](https://pre-commit.com/#install) tool to check and automatically fix any formatting issue before creating a git commit.

Run the following command to install pre-commit into your git hooks and have it run on every commit:

```shell
pre-commit install
```

For more information on how it works, see the `.pre-commit-config.yaml` configuration file.

Saleor has a strict formatting policy enforced by the [black formatting tool](https://github.com/python/black).

Module names should make their purpose obvious. Avoid generic file names such as `utils.py`.

### Linters

Use [black](https://github.com/python/black/) to make sure your code is correctly formatted.

Use [isort](https://github.com/timothycrosley/isort) to maintain consistent imports.

Use [pylint](https://www.pylint.org/) with the `pylint-django` plugin to catch errors in your code.

Use [pycodestyle](http://pycodestyle.pycqa.org/en/latest/) to make sure your code adheres to PEP 8.

Use [pydocstyle](http://pydocstyle.pycqa.org/en/latest/) to check that your docstrings are properly formatted.

## EditorConfig

[EditorConfig](http://editorconfig.org/) is a standard configuration file that aims to ensure consistent style across multiple programming environments.

Saleor’s repository contains [an `.editorconfig` file](https://github.com/mirumee/saleor/blob/master/.editorconfig) describing our formatting requirements.

Most editors and IDEs support this file either directly or via plugins. See the [list of supported editors and IDEs](http://editorconfig.org/#download) for detailed instructions.

If you make sure that your programming environment respects the contents of this file, you will automatically get correct indentation, encoding, and line endings.

## Git commit messages

To speed up the review process and to keep the logs tidy, we recommend the following simple rules on how to write good commit messages:

### Summary line

- It should contain less than 50 characters. It is best to make it short
- Introduce what has changed, using imperatives: fix, add, modify, etc.

### Description

- Add extra explanation if you feel it will help others to understand the summary content
- If you want, use bullet points (each bullet beginning with a hyphen or an asterisk)
- Avoid writing in one line. Use line breaks so the reader does not have to scroll horizontally

*Tip*: To ease review, try to limit your commits to a single, self-contained issue. This will also help others to understand and manage them in the future.


For more information and tips on how to write good commit messages, see the GitHub [guide](https://github.com/erlang/otp/wiki/writing-good-commit-messages).
