# Enterprise Service Level Agreement (SLA)
**Source:** sla_agreement.md | **Version:** v2.0 | **Section:** Operations

## Service Uptime Commitment
We guarantee a monthly service uptime of 99.99% for all Enterprise tier client accounts. Uptime is measured using global synthetic monitoring probes testing core API latency.

## Service Credits & Outages
In the event that monthly uptime falls below our 99.99% commitment, clients are eligible for service credits applied to their subsequent invoice:
- Uptime < 99.99% but >= 99.90%: 10% monthly service credit.
- Uptime < 99.90%: 25% monthly service credit.

Outages are calculated based on consecutive minutes of 5xx HTTP response codes or complete packet loss. To claim credits, notify your Client Relations Manager within 30 days of the incident.