# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-01-27

### Fixed
- **Ibercaja scraper robustness**: Improved table detection with multiple fallback selectors
- Added debug output (URL, title, buttons, links) when table not found
- Auto-dismiss additional popups/modals that may appear after login
- Multiple selector attempts for download button

## [1.2.0] - 2026-01-27

### Added
- **Ibercaja auto-sync scheduler**: Schedule automatic download and sync to Actual Budget at configurable intervals (1h, 3h, 6h, 12h, 24h)
- Shows scheduler status: next run time, last run time, and last result
- Prerequisites check: requires stored credentials and sync mapping before enabling
- "Run now" option to trigger immediate sync while scheduler is active

## [1.1.11] - 2026-01-27

### Fixed
- **Revert input changes**: Restored `type='password'` with `inputmode='numeric'` and `pattern='[0-9]*'` which was working correctly before

## [1.1.10] - 2026-01-27

### Fixed
- **ING input type**: PyWebIO doesn't support `type='tel'`, changed to `type='text'` with `inputmode='numeric'`

## [1.1.9] - 2026-01-26

### Fixed
- **Ibercaja Excel parsing**: Auto-detect header row instead of hardcoded row 6. Handles different Excel formats and maps column name variations
- **Reconnection banner**: Banner now dismissible by tap, and properly removes itself when WebSocket reconnects
- **CSV validation**: Added column validation before sync to provide clear error messages when CSV structure is incorrect

### Changed
- **Activity indicator**: Simplified to text-based indicator for better WebSocket compatibility
- **Added TODO.md**: Roadmap file with planned improvements for version control

## [1.1.8] - 2026-01-26

### Fixed
- **ING scraper exception handling**: Replaced bare `except:` clauses with specific exception types (`TimeoutError, Exception`) for better error visibility and debugging. This prevents silent failures and makes troubleshooting easier
- **Code quality**: Improved error messages to include exception type for easier diagnosis

### Changed
- **Branch cleanup**: Removed obsolete feature branches merged into main

## [1.1.6] - 2026-01-26

### Added
- **Activity indicator**: ASCII spinner (braille characters) shows when operations are running, confirming WebSocket connection is active

### Fixed
- **WebSocket reconnection**: Now reconnects automatically without reloading the page, preserving execution context and logs
- **Server configuration**: Added 60-second reconnection timeout to allow automatic reconnection after network interruptions

## [1.1.5] - 2026-01-26

### Fixed
- **ING app link styling**: Now matches other app buttons (transparent background with orange text instead of solid orange button)
- **ING app link functionality**: Opens ING website directly in new tab (more reliable than URL scheme approach)
- **Mobile numeric keyboard**: DNI and birthdate inputs now show numeric keyboard on mobile devices (matching PIN input behavior)

## [1.1.4] - 2025-01-26

### Added
- **ING app quick link**: When mobile 2FA validation is required, shows a clickable button to open the ING app directly. Uses `ingdirect://` URL scheme with fallback to website

## [1.1.3] - 2025-01-26

### Fixed
- **Mobile numeric keyboard**: ING PIN input now shows numeric keyboard on mobile while keeping password masking
- **Mobile WebSocket reconnection**: Added detection for when user returns to app after switching (e.g., to bank app for 2FA). Shows reconnect banner if connection dropped after 5+ seconds away

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
