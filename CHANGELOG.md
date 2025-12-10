<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]

## [0.1.3]

## Fixed

- Package the JavaScript file.

## Changed

- Now using _jxa-lib_ and _jxa-types_ in the TypeScript code.

## [0.1.2]

### Added

- Allow FLAC files to be added with the `--flac` flag. These files will get synchronised but Music
  will likely ignore them.

### Changed

- Added default platform-specific value for the split CUE cache directory.

### Fixed

- Only split CUE/MP3 and not CUE/FLAC, etc.

## [0.1.1]

### Changed

- Files with invalid CUE files will be skipped rather than including the full MP3.

### Fixed

- Split MP3 files will always have a 2 digit suffix.

## [0.1.0]

Revised version.

## [0.0.1]

First version.

[unreleased]: https://github.com/Tatsh/clem2itunes/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/Tatsh/clem2itunes/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/Tatsh/clem2itunes/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/Tatsh/clem2itunes/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/Tatsh/clem2itunes/releases/tag/v0.0.1
