# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2026-03-22

### Security
- Fixed 29 known vulnerabilities in Python dependencies:
  - starlette>=0.47.2 (CVE-2024-47874, CVE-2025-54121)
  - python-multipart>=0.0.18 (CVE-2024-53981, CVE-2026-24486)
  - python-jose>=3.4.0 (PYSEC-2024-233, PYSEC-2024-232)
  - pillow>=12.1.1 (CVE-2026-25990)
- Updated requirements.txt with explicit security patch versions

## [1.0.1] - 2026-03-22

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
