# API Developer Authentication Guide
**Source:** api_developer_guide.md | **Version:** v4.2 | **Section:** Authentication

## Header Setup & 401 Troubleshooting
All REST API requests to the enterprise system must be authenticated. Authentication requires passing an API secret key inside the HTTP headers. The system expects exact string matching in the following format:

```http
Authorization: Bearer <API_KEY>
```

A common cause of `401 Unauthorized` errors is omitting the "Bearer " prefix or using an expired secret key. Ensure that your client configuration block has headers defined precisely:
```json
{
  "headers": {
    "Authorization": "Bearer env.API_SECRET_KEY"
  }
}
```

If your API key expires, regenerate it from the Developer Console > API Keys. Net-new keys take approximately 60 seconds to propagate globally.