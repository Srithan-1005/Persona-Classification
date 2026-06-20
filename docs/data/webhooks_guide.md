# Webhook Setup & Event Subscriptions
**Source:** webhooks_guide.md | **Version:** v2.3 | **Section:** Developer Tools

Webhooks allow you to receive real-time HTTP POST notifications.
To set up a webhook:
1. Navigate to Developer Console > Webhooks.
2. Add your listener URL (e.g. `https://yourdomain.com/webhook`).
3. Select events to subscribe (e.g., `payment.success`, `user.created`).
Ensure your webhook handler returns an HTTP 200 response code within 3000ms to avoid retry queues.