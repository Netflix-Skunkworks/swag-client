Changelog
=========

0.3.0 - 2017-11-15
------------------

- Added the ability to test-run changes via the dry-run keyword.
- Fixed get_service_enabled function such that both v1 and v2 formats are correctly handled.
- Added v1 support to the get_service function.
- Upgrade click_log and moved to a application configuration object for CLI.
- Added a list_service command to CLI.
- Added a deploy_service command to CLI.
- Moved caching to a backend controlled option.