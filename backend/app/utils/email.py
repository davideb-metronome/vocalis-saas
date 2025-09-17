"""
Email utility - supports SMTP (MailHog) and Resend
"""

import asyncio
import smtplib
from email.message import EmailMessage
from typing import Optional
import httpx
from app.core.config import settings


def _build_welcome_html(first_name: str, credits: int, trial_days: int, trial_end_date: Optional[str]) -> str:
    dashboard_url = settings.DASHBOARD_URL
    docs_url = settings.DOCS_URL
    name = first_name or "there"
    end_str = f"Trial ends on <strong>{trial_end_date}</strong> (UTC)." if trial_end_date else ""
    minutes = max(1, credits // 1000)
    return f"""
<!doctype html>
<html><body style='margin:0;padding:0;background:#f7f9fc;font-family:Inter,system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1f2937;'>
  <table role='presentation' width='100%' cellpadding='0' cellspacing='0' style='background:#f7f9fc;padding:24px 0;'>
    <tr><td align='center'>
      <table role='presentation' width='600' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;padding:28px;border:1px solid #e5e7eb;'>
        <tr><td style='text-align:center;padding-bottom:8px;'><div style='display:inline-block;background:#1e88e5;color:#fff;border-radius:12px;padding:6px 10px;font-weight:700;'>VOCALIS</div></td></tr>
        <tr><td style='font-size:24px;font-weight:800;color:#111827;text-align:center;'>Welcome to Vocalis! 🎉</td></tr>
        <tr><td style='height:8px;'></td></tr>
        <tr><td style='font-size:16px;color:#374151;'>Hey {name},<br><br>Awesome! Your Vocalis account is ready. Here's what you got:</td></tr>
        <tr><td style='height:12px;'></td></tr>
        <tr><td>
          <div style='background:#eef6ff;border:1px solid #93c5fd;border-radius:12px;padding:20px;text-align:center;'>
            <div style='font-size:34px;font-weight:800;color:#1e3a8a'>{credits:,} credits</div>
            <div style='color:#64748b;font-size:14px;'>≈ {minutes} minutes of voice generation</div>
          </div>
        </td></tr>
        <tr><td style='height:16px;'></td></tr>
        <tr><td style='font-size:14px;color:#111827;font-weight:700;'>What you can do with your credits:</td></tr>
        <tr><td style='height:8px;'></td></tr>
        <tr><td style='font-size:14px;color:#4b5563;'>
          <ul style='margin:0 0 0 18px;padding:0;'>
            <li>Standard voices: 1,000 characters = 1,000 credits</li>
            <li>Premium voices: celebrity & emotional voices at 2× rate</li>
            <li>Voice cloning: create your custom voice (25,000 credit setup)</li>
          </ul>
        </td></tr>
        <tr><td style='height:12px;'></td></tr>
        <tr><td style='font-size:13px;color:#6b7280;'>{end_str}</td></tr>
        <tr><td style='height:16px;'></td></tr>
        <tr><td><a href='{dashboard_url}' style='display:inline-block;background:#1e88e5;color:#fff;text-decoration:none;font-weight:600;padding:12px 18px;border-radius:8px;'>Start Creating Voices →</a></td></tr>
        <tr><td style='height:16px;'></td></tr>
        <tr><td style='font-size:13px;color:#6b7280;'>Questions? Just reply to this email. Need help? <a href='{docs_url}' style='color:#1e88e5;text-decoration:none;'>Read the docs</a>.</td></tr>
      </table>
      <div style='font-size:12px;color:#9ca3af;margin-top:12px;'>© Vocalis. All rights reserved.</div>
    </td></tr>
  </table>
</body></html>
"""


def _build_text_fallback(first_name: str, credits: int, trial_days: int, trial_end_date: Optional[str]) -> str:
    name = first_name or "there"
    end_line = f"Trial ends on {trial_end_date} (UTC)." if trial_end_date else ""
    return (
        f"Hi {name},\n\n"
        f"Your Vocalis trial is active with {credits:,} credits for {trial_days} days.\n"
        f"{end_line}\n\n"
        "Tips:\n- Standard voices: 1 credit/character\n- Premium voices: 2 credits/character\n\n"
        f"Get started: {settings.DASHBOARD_URL}\n"
        f"Docs: {settings.DOCS_URL}\n"
    )


def _send_smtp(subject: str, to: str, html: str, text: Optional[str] = None):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg.set_content(text or "")
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        s.send_message(msg)


async def _send_resend(subject: str, to: str, html: str, text: Optional[str] = None):
    api_key = settings.RESEND_API_KEY
    if not api_key:
        raise RuntimeError("RESEND_API_KEY not configured")
    payload = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if text:
        payload["text"] = text
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post("https://api.resend.com/emails", headers=headers, json=payload)
        if resp.status_code not in (200, 202):
            raise RuntimeError(f"Resend error: {resp.status_code} {resp.text}")


async def send_welcome_email(to: str, first_name: str, credits: int, trial_days: int, trial_end_date: Optional[str] = None):
    subject = "Welcome to Vocalis — your trial is live"
    html = _build_welcome_html(first_name, credits, trial_days, trial_end_date)
    text = _build_text_fallback(first_name, credits, trial_days, trial_end_date)

    provider = (settings.EMAIL_PROVIDER or "smtp").lower()
    if provider == "smtp":
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _send_smtp, subject, to, html, text)
    elif provider == "resend":
        await _send_resend(subject, to, html, text)
    else:
        raise RuntimeError(f"Unknown EMAIL_PROVIDER: {settings.EMAIL_PROVIDER}")


async def send_conversion_email(to: str, first_name: str, days_left: int, trial_end_date: Optional[str] = None):
    subject = f"{days_left} days left — keep creating with Vocalis (20% off)"
    name = first_name or "there"
    end_line = f"Trial ends on <strong>{trial_end_date}</strong>." if trial_end_date else ""
    html = f"""
<!doctype html>
<html><body style='margin:0;padding:0;background:#f7f9fc;font-family:Inter,system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1f2937;'>
  <table role='presentation' width='100%' cellpadding='0' cellspacing='0' style='background:#f7f9fc;padding:24px 0;'>
    <tr><td align='center'>
      <table role='presentation' width='600' cellpadding='0' cellspacing='0' style='background:#fff;border-radius:12px;padding:28px;border:1px solid #e5e7eb;'>
        <tr><td style='font-size:22px;font-weight:800;color:#111827;'>Your trial ends in {days_left} days</td></tr>
        <tr><td style='height:8px;'></td></tr>
        <tr><td style='font-size:16px;color:#374151;'>Hi {name},<br><br>Keep creating with Vocalis — upgrade now and enjoy <strong>20% off</strong> your first month.</td></tr>
        <tr><td style='height:16px;'></td></tr>
        <tr><td><a href='{settings.DASHBOARD_URL.replace('/dashboard','/billing') + '?promo=TRIAL20'}' style='display:inline-block;background:#1e88e5;color:#fff;text-decoration:none;font-weight:600;padding:12px 18px;border-radius:8px;'>See Plans</a></td></tr>
        <tr><td style='height:12px;'></td></tr>
        <tr><td style='font-size:13px;color:#6b7280;'>{end_line}</td></tr>
      </table>
      <div style='font-size:12px;color:#9ca3af;margin-top:12px;'>© Vocalis. All rights reserved.</div>
    </td></tr>
  </table>
</body></html>
"""
    text = f"Hi {name},\n\nYour Vocalis trial ends in {days_left} days. Upgrade now for 20% off. {('Trial ends on ' + trial_end_date) if trial_end_date else ''}\n"

    provider = (settings.EMAIL_PROVIDER or "smtp").lower()
    if provider == "smtp":
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _send_smtp, subject, to, html, text)
    elif provider == "resend":
        await _send_resend(subject, to, html, text)
    else:
        raise RuntimeError(f"Unknown EMAIL_PROVIDER: {settings.EMAIL_PROVIDER}")
