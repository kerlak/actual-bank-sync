# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.2] - 2025-01-25

### Added
- **Favicon**: Custom SVG favicon with sync arrows and $ symbol in brand colors
- **Web title**: Proper "Banking Hub" title in browser tab

### Fixed
- **Dark theme consistency**: Fixed input-container elements displaying white background instead of dark theme

## [1.1.1] - 2025-01-25

### Fixed
- **playwright-stealth compatibility**: Fixed ImportError with playwright-stealth 2.0.0+ which changed its API from `stealth_sync(page)` to `Stealth().apply_stealth_sync(context)`. The code now handles both old and new API versions.

## [1.1.0] - 2025-01-24

### Added
- **Interactive file and account selection**: Users can now select Actual Budget file and account through the web interface during sync
- **Per-file encryption password**: Encryption passwords are now requested per file instead of globally, allowing different files to have different encryption keys
- **Saved mappings**: File and account selections are automatically saved after successful sync and can be reused in future syncs
- **Centralized credentials management**: New `[manage credentials]` option in main menu to view and manage all credentials and mappings in one place
- Helper functions in `actual_sync.py`:
  - `list_budget_files()`: Lists all available budget files in Actual Budget server
  - `list_accounts()`: Lists all accounts in a specific budget file

### Changed
- `sync_csv_to_actual()` now accepts optional `account_name` parameter for direct account specification
- Main menu now includes `[manage credentials]` button
- Bank-specific interfaces (Ibercaja, ING) simplified to focus on core operations (download, upload, sync)
- Removed individual `[clear credentials]` and `[clear mappings]` buttons from bank interfaces

### Fixed
- Multiple budget files can now be managed with different encryption passwords
- Account selection is more flexible and doesn't rely on hardcoded mappings

### Home Assistant Compatibility
- **100% backward compatible** with existing Home Assistant add-on configuration
- `ACTUAL_BUDGET_FILE` environment variable (from HA config) is automatically detected and pre-selected as default
- Legacy `account_mapping` from config is pre-selected if it matches an existing account
- No configuration changes required for existing Home Assistant users

### Migration Guide
For users upgrading from 1.0.0:
1. **Standalone users**: No action needed. First sync will prompt for file/account selection, then save for future use.
2. **Home Assistant users**: No action needed. Existing configuration (`actual_budget_file_id` and default account names) will be automatically detected and pre-selected.
3. **To change saved mappings**: Use the new `[manage credentials]` menu option.

## [1.0.0] - 2024-XX-XX

### Initial Release
- Automatic download of bank movements from Ibercaja and ING
- Manual Excel file upload support
- CSV conversion for Actual Budget import
- Basic sync functionality with hardcoded file and account mappings
- Home Assistant add-on support
- Web UI on port 2077
