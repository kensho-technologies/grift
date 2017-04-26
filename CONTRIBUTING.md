# Contributing

Thank you for taking the time to contribute to this project! Please open any pull requests against the **dev branch**.

## Code of Conduct

This project adheres to the Contributor Covenant [code of conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code.
Please report unacceptable behavior to grift-maintainer@kensho.com.

## Contributor License Agreement

Each contributor is required to agree to our Contributor License Agreement, to ensure that their contribution may be safely merged into the project codebase and released under the existing code license. This agreement does not change contributors' rights to use the contributions for any other purpose -- it is simply used for the protection of both the contributors and the project.

## Style Guide

Make sure your code conforms to style by running `pycodestyle grift/` This should pass with no warnings (see our custom configuration in the `[pycodestyle]` section of `setup.cfg`).

Use `bandit` to check your code for common Python bugs and security vulnerabilities. Running it as `bandit -r grift/` on the source code of the package should not detect any issues.

