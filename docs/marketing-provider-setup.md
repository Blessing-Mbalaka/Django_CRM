# Marketing provider setup

Marketing is served at `/growth/`. Planning, uploads, leads, calendars, analytics, previews, and Brand Kit features work without external credentials. Each channel reports **Not configured** until its own environment variables are present; one unavailable provider does not disable the others.

Never commit `.env`, copy credentials into Django settings, expose them in browser configuration, or paste them into Marketing records. Start from `.env.example` and use the hosting platform's secret manager in production.

## Twilio Email

Set `TWILIO_EMAIL_API_KEY`, `TWILIO_EMAIL_API_SECRET`, `TWILIO_EMAIL_FROM_ADDRESS`, and `TWILIO_EMAIL_FROM_NAME`. Create dedicated Email API credentials and verify the sender/domain before testing. Email uses API-key Basic Auth against `https://comms.twilio.com/v1/Emails`; it does not use the primary Account SID/Auth Token pair. See the official [Twilio Email getting-started guide](https://www.twilio.com/docs/email/api/getting-started) and [Mail Send API](https://www.twilio.com/docs/email/api/mail-send).

## Twilio SMS

Set `TWILIO_ACCOUNT_SID`, `TWILIO_API_KEY`, `TWILIO_API_SECRET`, and `TWILIO_AUTH_TOKEN`. Configure exactly one sender using `TWILIO_SMS_FROM_NUMBER` or `TWILIO_MESSAGING_SERVICE_SID`. Set `TWILIO_STATUS_CALLBACK_URL` to the public HTTPS URL ending in `/growth/webhooks/twilio/sms/`. Trial-account recipient restrictions still apply.

Use the official [API key guide](https://www.twilio.com/docs/iam/api-keys), [Message resource reference](https://www.twilio.com/docs/messaging/api/message-resource), [status callback guide](https://www.twilio.com/docs/messaging/guides/track-outbound-message-status), and [webhook security guide](https://www.twilio.com/docs/usage/webhooks/webhooks-security).

## Meta shared settings

Set `META_GRAPH_API_VERSION` to a supported pinned version, `META_APP_SECRET` from the app dashboard, and `META_WEBHOOK_VERIFY_TOKEN` to a private random value chosen for this deployment. Configure Meta's callback as the public HTTPS URL ending in `/growth/webhooks/meta/`. The GET challenge uses the verify token; event POSTs require a valid `X-Hub-Signature-256` HMAC. Review upgrades in the official [Graph API changelog](https://developers.facebook.com/docs/graph-api/changelog/).

### WhatsApp Cloud API

Set `META_ACCESS_TOKEN`, `META_WHATSAPP_PHONE_NUMBER_ID`, and `META_WHATSAPP_BUSINESS_ACCOUNT_ID`. Development tokens are short-lived. Production should use an appropriately scoped long-lived/system-user token and approved templates where required. See Meta's official [WhatsApp Business Platform collection](https://www.postman.com/meta/whatsapp-business-platform/).

### Facebook Page publishing

Set `META_FACEBOOK_PAGE_ID` and `META_FACEBOOK_PAGE_ACCESS_TOKEN` with approved Page permissions. The integration publishes only to the configured Page; it does not post to personal profiles or purchase advertising. See the official [Pages API posts guide](https://developers.facebook.com/docs/pages-api/posts/).

### Instagram Professional publishing

Set `META_INSTAGRAM_USER_ID` and `META_INSTAGRAM_ACCESS_TOKEN` for a connected Professional account with approved publishing permissions. Set `MARKETING_PUBLIC_BASE_URL` to the public HTTPS origin. Images remain previewable locally, but publishing is unavailable unless their URLs are publicly reachable over HTTPS. See the official [Instagram content-publishing guide](https://developers.facebook.com/docs/instagram-platform/content-publishing/) and [Meta Instagram collection](https://www.postman.com/meta/instagram/).

## Safe verification

1. Run `python manage.py check` and open `/growth/`; confirm only configured channels change from **Not configured** to **Available**.
2. Create a dedicated consented test contact. Never use a real customer list for initial verification.
3. Preview first, then test one channel and destination at a time in the provider's trial/test environment.
4. Confirm the message first shows `accepted`; only a signed provider event should advance it to `sent`, `delivered`, or `read`.
5. Remove the test contact or revoke its consent after verification.

Automated tests mock every provider call and must never perform a real send or publication.

## Scheduling

Run due jobs with a bounded batch:

```text
python manage.py send_due_marketing --limit 100
```

The dispatcher transactionally claims rows, recovers stale claims, isolates failures, and prevents an already-claimed message from being sent twice.

- Windows Task Scheduler: use the virtual environment's `python.exe`, arguments `manage.py send_due_marketing --limit 100`, and the project folder as **Start in**.
- cron: use absolute paths for the virtual environment Python and `manage.py`, with normal platform log redirection.
- Managed hosting: configure the same command as a scheduled job with the same environment variables as the web application.

## Permissions and consent

CEO, Director, and System Administrator roles may change Marketing data, send, schedule, retry, cancel, modify the Brand Kit, and convert leads to CRM clients. Other authenticated users are read-only. Email, SMS, and WhatsApp require affirmative consent for that channel, an active contact, a usable destination, and no opt-out timestamp. Validation occurs before provider I/O.
