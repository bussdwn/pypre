# Changelog

## 1.3.1 - 2023-02-26

- Ask for AES passphrase when decryption failed.

## 1.3.0 - 2023-02-21

- Configuration file can be encrypted using AES.
- Added `typing-extensions` as a dependency, and fixed some type hints.

## 1.2.4 - 2023-02-15

- Clarify available settings in README, and added some example commands

## 1.2.3 - 2023-01-14

- Fix a few typos

## 1.2.2 - 2022-12-29

- Fix a few typos
- Update .gitignore

## 1.2.1 - 2022-12-28

- Add missing `__future__` import

## 1.2.0 - 2022-12-28

- Remove `click_path` from requirements, use a local version of `GlobPaths`
- Make package fully typed (`--strict`)
- Remove alternative help options. Only `--help` can now be used
- Use a line length of 120 for black
- Fix a few typos
- Update CBFTP url in README

## 1.1.0 - 2022-11-30

- Refactor logging. No custom `Logger` is used
- Fixed some typing related stuff
- Remove usage of `coloredlogs`
- Switch from `pytomlpp` to `tomli`

## 1.0.1 - 2022-10-29

- Fix connection check to the cbftp instance

## 1.0.0 - 2022-10-27

- Use pydantic to manage and validate configuration
- Make pypre fully typed, and mypy compliant
- Format the code using [black](https://github.com/psf/black)

## 0.2.0 - 2022-10-21

- Use the `/path` API endpoint instead of sending a raw command
- Use `pathlib.PurePosixPath` instead of `pathlib.PosixPath`, so that the tool can still be used on Windows
- Moved the changelog to a separate file

## 0.1.1 - 2022-07-21

- Added a `--check` option (WIP)
- Fixed some typings

## 0.1.0 - 2022-07-15

- Initial release.
