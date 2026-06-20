# CORS Policy Setup Guide
**Source:** cors_configuration_guide.md | **Version:** v1.5 | **Section:** Web Server

Cross-Origin Resource Sharing (CORS) errors occur when browser requests are blocked from foreign domains. To resolve CORS issues:
Ensure the server headers include:
`Access-Control-Allow-Origin: *` (or specify your absolute domain: `https://app.enterprise.com`)
`Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
`Access-Control-Allow-Headers: Content-Type, Authorization`