# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- CI/CD workflow updated from Node.js to Python (appropriate for FastAPI project)
- Added Python 3.10, 3.11, 3.12 to testing matrix

### Changed
- Updated Python dependencies:
  - fastapi: >=0.110 -> >=0.115.0
  - uvicorn: >=0.23 -> >=0.30.0
  - pydantic: >=2.0 -> >=2.5.0
  - aiosqlite: >=0.19.0 -> >=0.20.0
- Added additional dependencies: python-multipart, python-jose[cryptography], passlib[bcrypt]

## [1.0.0] - 2026-03-21

### Added
- Initial release
- Core functionality implemented
- Basic documentation

### Security
- Repository security improvements
