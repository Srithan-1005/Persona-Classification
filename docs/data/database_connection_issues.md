# Database Connection & Timeout Settings
**Source:** database_connection_issues.md | **Version:** v2.0 | **Section:** Testing

## Database Connection Timeout Thresholds
The default database timeout threshold is set to 3000ms. Do not increase this timeout threshold under normal operating conditions. Setting timeouts higher can lead to database thread pool exhaustion and memory leaks.

If queries fail frequently with timeout errors, inspect database indexes and optimize queries rather than increasing the timeout limit.