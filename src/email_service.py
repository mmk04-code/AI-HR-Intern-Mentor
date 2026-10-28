"""
Email service module for Internship Task Review Assistant.
Generates comprehensive feedback emails and handles both Real SMTP sending
and Simulated Demo Mode with persistent audit logging.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Tuple, Optional

from src.database import log_email
from src.config import get_email_credentials, has_email_configured


def is_smtp_configured() -> bool:
    """Check if valid SMTP settings are provided in environment variables."""
    return has_email_configured()


def generate_feedback_email_content(
    candidate_name: str,
    module_name: str,
    task_title: str,
    review_status: str,
    review_score: int,
    strengths: list,
    missing_items: list,
    actionable_corrections: list,
    review_date: Optional[str] = None,
    review_time: Optional[str] = None,
    session_link: Optional[str] = None,
    reviewer_message: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Generate professional email subject, plain text body, and HTML body.
    """
    subject = f"[Review Feedback] {module_name} - {task_title} ({review_status})"

    strengths_text = "\n".join([f"  • {s}" for s in strengths[:4]]) or "  • Work submitted and reviewed."
    missing_text = "\n".join([f"  • {m}" for m in missing_items[:4]]) or "  • None identified."
    corrections_text = "\n".join([f"  • {c}" for c in actionable_corrections[:4]]) or "  • Follow review recommendations."

    schedule_text = ""
    if review_date and review_time:
        schedule_text = (
            f"\n--- NEXT REVIEW SESSION ---\n"
            f"Date & Time: {review_date} at {review_time} (Local Time)\n"
            f"Meeting Link: {session_link or 'Will be shared separately'}\n"
        )
        if reviewer_message:
            schedule_text += f"Reviewer Note: {reviewer_message}\n"

    # Plain text version
    body_text = f"""Dear {candidate_name},

Thank you for your recent submission for "{module_name}: {task_title}".
Our technical review has been completed. Below is your detailed feedback summary:

--- REVIEW OUTCOME ---
Status: {review_status.upper()}
Overall Evaluation Score: {review_score} / 100

--- STRENGTHS & COMPLETED ITEMS ---
{strengths_text}

--- AREAS REQUIRING ATTENTION & MISSING ITEMS ---
{missing_text}

--- ACTIONABLE CORRECTIONS FOR NEXT REVISION ---
{corrections_text}
{schedule_text}
Please review this feedback, implement the necessary corrections, and submit your updated revision through the portal prior to the scheduled session.

Best regards,
Technical Review Team & Internship Coordinator
"""

    # HTML version
    strengths_html = "".join([f"<li>{s}</li>" for s in strengths[:4]]) or "<li>Work submitted and reviewed.</li>"
    missing_html = "".join([f"<li>{m}</li>" for m in missing_items[:4]]) or "<li>None identified.</li>"
    corrections_html = "".join([f"<li>{c}</li>" for c in actionable_corrections[:4]]) or "<li>Follow review recommendations.</li>"

    schedule_html = ""
    if review_date and review_time:
        schedule_html = f"""
        <div style="background-color: #f0f7ff; border-left: 4px solid #1a73e8; padding: 12px 16px; margin: 20px 0; border-radius: 4px;">
            <h3 style="margin-top: 0; color: #1a73e8;">Next Review Session</h3>
            <p style="margin: 4px 0;"><strong>Date & Time:</strong> {review_date} at {review_time} (Local Time)</p>
            <p style="margin: 4px 0;"><strong>Session Link:</strong> <a href="{session_link or '#'}" target="_blank">{session_link or 'To be announced'}</a></p>
            {f'<p style="margin: 4px 0;"><em>Reviewer Note: {reviewer_message}</em></p>' if reviewer_message else ''}
        </div>
        """

    status_color = "#10b981" if review_status == "Completed" else ("#f59e0b" if review_status == "Needs Changes" else "#ef4444")

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #202124; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;">Internship Task Review Feedback</h2>
        <p>Dear <strong>{candidate_name}</strong>,</p>
        <p>Your submission for <strong>{module_name}: {task_title}</strong> has been evaluated. Below is the summary of your review:</p>

        <div style="display: flex; gap: 15px; margin: 15px 0;">
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px 18px; flex: 1;">
                <div style="font-size: 12px; color: #6b7280; text-transform: uppercase;">Status</div>
                <div style="font-size: 18px; font-weight: bold; color: {status_color};">{review_status}</div>
            </div>
            <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px 18px; flex: 1;">
                <div style="font-size: 12px; color: #6b7280; text-transform: uppercase;">Score</div>
                <div style="font-size: 18px; font-weight: bold; color: #1f2937;">{review_score} / 100</div>
            </div>
        </div>

        <h3 style="color: #166534; margin-top: 20px;">✓ Strengths & Completed Items</h3>
        <ul style="padding-left: 20px; color: #374151;">{strengths_html}</ul>

        <h3 style="color: #991b1b; margin-top: 20px;">⚠ Areas Requiring Attention</h3>
        <ul style="padding-left: 20px; color: #374151;">{missing_html}</ul>

        <h3 style="color: #1e40af; margin-top: 20px;">⚡ Actionable Corrections</h3>
        <ul style="padding-left: 20px; color: #374151;">{corrections_html}</ul>

        {schedule_html}

        <p style="margin-top: 25px;">Please implement the requested changes and submit your revision through the portal.</p>
        <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 25px 0;" />
        <p style="font-size: 12px; color: #6b7280;">Internship Technical Evaluation System • Automated Notification</p>
    </body>
    </html>
    """

    return subject, body_text, body_html


def send_or_simulate_email(
    review_id: int,
    recipient_email: str,
    subject: str,
    body_text: str,
    body_html: str,
    force_simulation: bool = False,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email via SMTP if configured and not force_simulation;
    otherwise record as SIMULATED — NOT SENT in database logs.
    """
    if force_simulation or not is_smtp_configured():
        # Demo / Simulated Mode
        status = "SIMULATED — NOT SENT"
        log_id = log_email(
            review_id=review_id,
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            mode="SIMULATED",
            status=status,
            error_message="SMTP not configured or demo mode selected; email was simulated safely.",
            db_path=db_path
        )
        return {
            "success": True,
            "mode": "SIMULATED",
            "status": status,
            "log_id": log_id,
            "message": "Demo mode: Email simulated and logged with status 'SIMULATED — NOT SENT'."
        }

    # Real SMTP Mode
    credentials = get_email_credentials()
    host = credentials["server"]
    port = credentials["port"]
    user = credentials["username"]
    password = credentials["password"]
    from_addr = credentials["from_address"] or user
    use_tls = credentials["use_tls"]

    server = None
    try:
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=12)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(host, port, timeout=12)
        server.login(user, password)
    except Exception as e:
        if server:
            try:
                server.quit()
            except Exception:
                pass
        status = "SIMULATED — NOT SENT"
        log_id = log_email(
            review_id=review_id,
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            mode="SIMULATED",
            status=status,
            error_message=f"SMTP connection or authentication failed before sending ({type(e).__name__}); email was simulated.",
            db_path=db_path
        )
        return {
            "success": True,
            "mode": "SIMULATED",
            "status": status,
            "log_id": log_id,
            "message": "SMTP was unavailable or rejected credentials; email was safely simulated and not sent."
        }

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = recipient_email
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))

        server.sendmail(from_addr, [recipient_email], msg.as_string())
        server.quit()

        status = "SENT"
        log_id = log_email(
            review_id=review_id,
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            mode="REAL",
            status=status,
            db_path=db_path
        )
        return {
            "success": True,
            "mode": "REAL",
            "status": status,
            "log_id": log_id,
            "message": f"Real email delivered successfully to {recipient_email}."
        }
    except Exception as e:
        status = "FAILED"
        err_msg = f"SMTP transmission failed ({type(e).__name__}); delivery was not confirmed."
        log_id = log_email(
            review_id=review_id,
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            mode="REAL",
            status=status,
            error_message=err_msg,
            db_path=db_path
        )
        return {
            "success": False,
            "mode": "REAL",
            "status": status,
            "log_id": log_id,
            "error": err_msg
        }
