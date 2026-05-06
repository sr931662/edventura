import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f4f6f9;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6f9;padding:32px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#ffffff;border-radius:8px;overflow:hidden;
                      box-shadow:0 2px 8px rgba(0,0,0,.08);">

          <!-- Header -->
          <tr>
            <td style="background:{primary_color};padding:24px 32px;">
              {logo_html}
              <span style="color:#ffffff;font-size:20px;font-weight:bold;
                           vertical-align:middle;">{sender_name}</span>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px;">
              <h2 style="margin:0 0 16px;color:#1a1a2e;font-size:20px;">{title}</h2>
              <p style="margin:0 0 24px;color:#444;font-size:15px;line-height:1.6;">
                {body}
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#f4f6f9;padding:20px 32px;
                       border-top:1px solid #e8ecf0;color:#888;font-size:12px;">
              {footer_html}
              <p style="margin:4px 0 0;">
                This is an automated message from <strong>{sender_name}</strong>.
                Please do not reply to this email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

_TEXT_TEMPLATE = """\
{sender_name}
{'=' * len(sender_name)}

{title}

{body}

---
This is an automated message from {sender_name}. Please do not reply.
"""


class EmailService:
    """Thin async SMTP sender.  Instantiate once per send or share across calls."""

    def __init__(
        self,
        sender_name: str | None = None,
        sender_email: str | None = None,
        primary_color: str = "#4f46e5",
        logo_url: str | None = None,
        footer_template: str | None = None,
    ):
        self.sender_name = sender_name or settings.SMTP_FROM_NAME
        self.sender_email = sender_email or settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        self.primary_color = primary_color
        self.logo_url = logo_url
        self.footer_template = footer_template

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def send(self, to_email: str, subject: str, body: str) -> bool:
        """Send a notification email.  Returns True on success, False on failure."""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured – email not sent to %s", to_email)
            return False

        try:
            msg = self._build_message(to_email, subject, body)
            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=settings.SMTP_TLS,
            )
            logger.info("Email delivered to %s | subject=%r", to_email, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s | subject=%r", to_email, subject)
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_message(self, to_email: str, subject: str, body: str) -> MIMEMultipart:
        logo_html = (
            f'<img src="{self.logo_url}" alt="{self.sender_name}" '
            f'height="36" style="vertical-align:middle;margin-right:10px;" />'
            if self.logo_url
            else ""
        )
        footer_html = (
            f"<p style='margin:0 0 4px;'>{self.footer_template}</p>"
            if self.footer_template
            else ""
        )

        html_body = _HTML_TEMPLATE.format(
            title=subject,
            body=body.replace("\n", "<br />"),
            sender_name=self.sender_name,
            primary_color=self.primary_color,
            logo_html=logo_html,
            footer_html=footer_html,
        )
        text_body = _TEXT_TEMPLATE.format(
            sender_name=self.sender_name,
            title=subject,
            body=body,
        )

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.sender_name} <{self.sender_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        return msg
