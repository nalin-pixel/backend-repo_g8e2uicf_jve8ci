from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

app = FastAPI(title="Active Control Automation API")

# CORS - allow frontend
frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*" if frontend_url == "*" else frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    message: str


@app.get("/test")
async def test():
    return {"ok": True}


def send_email(subject: str, body: str) -> bool:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    to_email = os.getenv("TO_EMAIL")

    if not (smtp_host and smtp_user and smtp_pass and to_email):
        # Missing configuration – act as a no-op but return False to indicate not actually sent
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Website Contact", smtp_user))
    msg["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


@app.post("/contact")
async def contact(payload: ContactRequest):
    subject = f"New Inquiry from {payload.name}"
    body_lines = [
        f"Name: {payload.name}",
        f"Email: {payload.email}",
        f"Phone: {payload.phone or '-'}",
        "",
        "Message:",
        payload.message,
    ]
    sent = send_email(subject, "\n".join(body_lines))
    # Always return OK so UI can show confirmation; include whether it was sent
    return {"ok": True, "sent": sent}
