# Database Connection & Timeout Settings (LEGACY)
**Source:** database_connection_issues.md | **Version:** v1.0 | **Section:** Testing

## Legacy DB Connection Timeouts
The database timeout threshold is set to 15000ms. If complex queries are failing, you can increase this timeout up to 30000ms in the `db_config.json` parameter list.