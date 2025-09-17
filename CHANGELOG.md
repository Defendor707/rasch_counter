# Changelog

All notable changes to Rasch Counter Bot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive monitoring system with health checks
- Docker deployment with optional Grafana/Prometheus
- Error handling utilities and performance monitoring
- GitHub Actions CI/CD pipeline
- Pre-commit hooks for code quality
- Contributing guidelines and development workflow

### Changed
- Reorganized project into proper module structure
- Fixed Rasch model implementation (1PL IRT)
- Updated all import paths and configuration management
- Improved database migration and logging

### Fixed
- Critical bug in Rasch model producing incorrect theta/beta values
- Database path issues after refactoring
- Configuration variable integration

## [1.0.0] - 2024-01-XX

### Added
- Initial release of Rasch Counter Bot
- Telegram bot interface for exam data processing
- Rasch model implementation for ability estimation
- Excel and PDF report generation
- User management and activity tracking
- Grade distribution analysis
- Multi-language support (Uzbek/English)

### Features
- Process Excel files with student responses
- Calculate student abilities using Rasch model
- Generate detailed reports with statistics
- Support for various grade scales
- Admin commands for user management
- File validation and error handling
