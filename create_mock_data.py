import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_pdf(filepath):
    print(f"Generating PDF: {filepath}")
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Enterprise Invoicing & Refund Policy Guide")
    
    # Metadata
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, height - 70, "Document Reference: REF-BILL-2026 | Version: v3.0 | Verified: June 2026")
    
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.line(50, height - 80, width - 50, height - 80)
    
    # Body Content
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 110, "1. Billing & Payment Protocols")
    
    c.setFont("Helvetica", 10)
    text = [
        "All subscription plans are billed on a recurring monthly or annual basis. Invoices are",
        "generated automatically at the start of each billing cycle. Payment is due within 14 days",
        "of invoice receipt. Enterprise accounts can request Net-30 invoice terms subject to credit approval.",
        "Accepted payment methods include Credit Cards (Visa, MasterCard, Amex), Wire Transfer, and ACH.",
    ]
    y = height - 130
    for line in text:
        c.drawString(60, y, line)
        y -= 15
        
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, "2. Refund Policy Guidelines (Sensitive Actions)")
    y -= 40
    
    text2 = [
        "Refunds can only be requested for subscription charges made within the last 14 calendar days.",
        "To request a refund, users must navigate to Billing Settings > Transactions and select",
        "'Request Refund'. Standard refunds take 5-10 business days to process and return to the",
        "original payment method. Note: Refund actions are classified as financially sensitive and",
        "automatically trigger compliance reviews. Enterprise accounts require supervisor approval",
        "for any single refund transaction exceeding $500. Subscriptions cancelled after 14 days",
        "are not eligible for pro-rated refunds but will remain active until the billing cycle ends.",
    ]
    for line in text2:
        c.drawString(60, y, line)
        y -= 15
        
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, "3. Compliance & Account Closure")
    y -= 40
    
    text3 = [
        "For security and auditing compliance, accounts in arrears for more than 45 days will be",
        "suspended. If you require full data deletion or GDPR-related account closure, please refer",
        "to the privacy settings or contact security@company.com directly.",
    ]
    for line in text3:
        c.drawString(60, y, line)
        y -= 15

    c.save()
    print("PDF generation complete.")

# 10+ Support articles to create
ARTICLES = {
    # 1. API authentication developer guide
    "api_developer_guide.md": """# API Developer Authentication Guide
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
""",

    # 2. Server Installation Setup
    "server_installation_setup.txt": """Server Installation & Port Configuration Setup
Source: server_installation_setup.txt | Version: v1.2 | Section: Infrastructure

Our enterprise service daemon runs on port 8080 by default. To modify this, you must edit the local configuration environment variables.
Open the environment file `.env` in your installation directory and define:
PORT=9000

After changing the port variable, restart the pm2 service runner:
pm2 restart ecosystem.config.js

Ensure your network security group rules allow traffic on port 9000. If traffic is blocked, check local firewalls (e.g. ufw or iptables) to verify ports are open.
""",

    # 3. SLA Service Level Agreement
    "sla_agreement.md": """# Enterprise Service Level Agreement (SLA)
**Source:** sla_agreement.md | **Version:** v2.0 | **Section:** Operations

## Service Uptime Commitment
We guarantee a monthly service uptime of 99.99% for all Enterprise tier client accounts. Uptime is measured using global synthetic monitoring probes testing core API latency.

## Service Credits & Outages
In the event that monthly uptime falls below our 99.99% commitment, clients are eligible for service credits applied to their subsequent invoice:
- Uptime < 99.99% but >= 99.90%: 10% monthly service credit.
- Uptime < 99.90%: 25% monthly service credit.

Outages are calculated based on consecutive minutes of 5xx HTTP response codes or complete packet loss. To claim credits, notify your Client Relations Manager within 30 days of the incident.
""",

    # 4. GDPR Compliance & Data Privacy
    "gdpr_privacy_policy.txt": """GDPR Privacy Policy & Data Deletion
Source: gdpr_privacy_policy.txt | Version: v2.1 | Section: Legal

Sensitive Action: Account data deletion and GDPR compliance.
Under General Data Protection Regulation (GDPR) Article 17 (Right to Erasure), users have the right to request absolute deletion of all PII (Personally Identifiable Information).
Data deletion requests are permanent and cannot be undone.

To request deletion:
1. Go to Account Settings > Privacy > Delete Account.
2. Verify via your email credentials.
3. Once submitted, compliance teams have 30 days to purge the records from active servers and backups.
Alternatively, email data-privacy@company.com with the subject line "GDPR Erasure Request".
""",

    # 5. Database Connection Issues
    "database_connection_issues.md": """# Database Connection & Timeout Settings
**Source:** database_connection_issues.md | **Version:** v2.0 | **Section:** Testing

## Database Connection Timeout Thresholds
The default database timeout threshold is set to 3000ms. Do not increase this timeout threshold under normal operating conditions. Setting timeouts higher can lead to database thread pool exhaustion and memory leaks.

If queries fail frequently with timeout errors, inspect database indexes and optimize queries rather than increasing the timeout limit.
""",

    # 6. Legacy Database Timeout (Conflict)
    "database_connection_legacy.md": """# Database Connection & Timeout Settings (LEGACY)
**Source:** database_connection_issues.md | **Version:** v1.0 | **Section:** Testing

## Legacy DB Connection Timeouts
The database timeout threshold is set to 15000ms. If complex queries are failing, you can increase this timeout up to 30000ms in the `db_config.json` parameter list.
""",

    # 7. CORS Configuration Guide
    "cors_configuration_guide.md": """# CORS Policy Setup Guide
**Source:** cors_configuration_guide.md | **Version:** v1.5 | **Section:** Web Server

Cross-Origin Resource Sharing (CORS) errors occur when browser requests are blocked from foreign domains. To resolve CORS issues:
Ensure the server headers include:
`Access-Control-Allow-Origin: *` (or specify your absolute domain: `https://app.enterprise.com`)
`Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
`Access-Control-Allow-Headers: Content-Type, Authorization`
""",

    # 8. Reset Password FAQ
    "reset_password_faq.txt": """Resetting Your Password
Source: reset_password_faq.txt | Version: v2.0 | Section: FAQs

To reset your account password, click the 'Forgot Password' link on the login page.
Enter your registered email address. You will receive an email with a secure link to choose a new password.
If you do not receive the email:
1. Check spam or junk folders.
2. Ensure browser cache is cleared.
3. Verify that your account is not locked due to multiple login failures.
""",

    # 9. Enterprise Integrations FAQ
    "enterprise_integrations.txt": """Enterprise Third-Party Integrations
Source: enterprise_integrations.txt | Version: v1.0 | Section: Features

We support native integrations with Salesforce, Slack, Jira, and HubSpot.
To activate integrations:
1. Go to Workspace Settings > Integrations.
2. Select the platform and click 'Authenticate'.
3. Follow the OAuth prompt to authorize connections.
Enterprise support plans include guided setup with an integration specialist.
""",

    # 10. Webhooks and Notifications
    "webhooks_guide.md": """# Webhook Setup & Event Subscriptions
**Source:** webhooks_guide.md | **Version:** v2.3 | **Section:** Developer Tools

Webhooks allow you to receive real-time HTTP POST notifications.
To set up a webhook:
1. Navigate to Developer Console > Webhooks.
2. Add your listener URL (e.g. `https://yourdomain.com/webhook`).
3. Select events to subscribe (e.g., `payment.success`, `user.created`).
Ensure your webhook handler returns an HTTP 200 response code within 3000ms to avoid retry queues.
""",

    # 11. Security Best Practices
    "security_best_practices.txt": """Security and Compliance Best Practices
Source: security_best_practices.txt | Version: v3.1 | Section: InfoSec

To maintain account safety:
- Never commit raw API keys or passwords in version control.
- Enable Multi-Factor Authentication (MFA) under Security settings.
- Implement Role-Based Access Control (RBAC) to limit member privileges.
- Regularly review audit logs for anomalous logins or configuration changes.
"""
}

def main():
    data_dir = "docs/data"
    os.makedirs(data_dir, exist_ok=True)
    
    # 1. Create PDF
    pdf_path = os.path.join(data_dir, "billing_and_refund_policy.pdf")
    create_pdf(pdf_path)
    
    # 2. Create Text and Markdown Articles
    for filename, content in ARTICLES.items():
        filepath = os.path.join(data_dir, filename)
        print(f"Writing article: {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
            
    print("Mock Knowledge Base creation finished successfully!")

if __name__ == "__main__":
    main()
