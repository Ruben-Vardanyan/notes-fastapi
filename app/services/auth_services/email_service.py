# notes-fastapi/app/services/auth_services/email_service.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def send_activation_email(email_to: str, username: str, token: str):
    """Logs into SMTP server and fires off the activation link email."""
    # Matches your path parameter update /{token}
    activation_url = f"{settings.API_BASE_URL}{settings.API_V1_STR}/auth/verify-email/{token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Activate Your Notes Account"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = email_to

    html_content = f"""
    <html>
        <body>
            <h3>Welcome to Notes, {username}!</h3>
            <p>Thank you for registering. Please click the link below to activate your account:</p>
            <p><a href="{activation_url}" style="padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">Activate Account</a></p>
            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p>{activation_url}</p>
            <small>This link will expire shortly.</small>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(settings.EMAIL_SERVER, settings.EMAIL_PORT)
        if settings.EMAIL_TLS:
            server.starttls()
        server.login(settings.EMAIL_FROM, settings.EMAIL_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, email_to, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")


def send_password_reset_email(email_to: str, username: str, token: str):
    """Fires a short-lived password recovery link directly to the user's inbox."""
    # Point this to your FRONTEND URL where the form will live!
    # For local development testing, you can use localhost:3000
    reset_url = f"{settings.FRONTEND_BASE_URL}/reset-password?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset Your Notes Account Password"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = email_to

    html_content = f"""
    <html>
        <body>
            <h3>Hello, {username}</h3>
            <p>We received a request to reset the password for your Notes account.</p>
            <p>Click the button below to set up a new password. <strong>This link is valid for 15 minutes only.</strong></p>
            <p><a href="{reset_url}" style="padding: 10px 20px; background-color: #DC3545; color: white; text-decoration: none; border-radius: 5px; display: inline-block;">Reset Password</a></p>
            <p>If you did not request this change, you can safely ignore this email.</p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;"/>
            <small style="color: #777;">For security, if the button doesn't work, copy-paste this link: {reset_url}</small>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(settings.EMAIL_SERVER, settings.EMAIL_PORT)
        if settings.EMAIL_TLS:
            server.starttls()
        server.login(settings.EMAIL_FROM, settings.EMAIL_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, email_to, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
