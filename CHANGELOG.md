# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### `Added` for new features

- Uses also `title`, `url` - i.e. header of an actual getPocket CSV export.
- Logs unsuccessful and doubtful downloads into url_retrieval.log.
- Coloured output for better orientation (BLUE = start, RED = wrong, GREEN = correct).

### `Changed` for changes in existing functionality

- Tags delimiters are `,` and `|`.
- Try to download directly, if previous attempts fail. Some pages block indirect attempts. Some pages really don't exist anymore.

### `Deprecated` for soon-to-be removed features

### `Removed` for now removed features

### `Fixed` for any bugfixes

### `Security` in case of vulnerabilities

## [0.1.0] - 2025-06-22

### Added

A simple Python tool to convert your Pocket export or any URL+label list into PDFs, organized by labels for easy offline backup.

[Unreleased]: https://github.com/WorkOfStan/web-pages-to-pdf/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/WorkOfStan/web-pages-to-pdf/releases/tag/v0.1.0
