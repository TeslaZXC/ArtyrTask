import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # For SSL
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_verification_email(to_email: str, code: str, purpose: str):
    print(f"\n[{purpose.upper()} CODE FOR {to_email}]: {code}\n")  # Fallback logging
    
    if not SMTP_USER or not SMTP_PASSWORD:
        print("SMTP_USER or SMTP_PASSWORD not set. Skipping real email sending. Use the code above.")
        return False
        
    msg = EmailMessage()
    
    if purpose == "register":
        msg.set_content(f"Ваш код для регистрации: {code}\nНикому не сообщайте этот код.")
        msg['Subject'] = 'Код подтверждения регистрации'
    elif purpose == "reset":
        msg.set_content(f"Ваш код для сброса пароля: {code}\nНикому не сообщайте этот код.")
        msg['Subject'] = 'Сброс пароля'
    else:
        msg.set_content(f"Ваш код: {code}")
        msg['Subject'] = 'Код подтверждения'

    msg['From'] = f"ArtyrTask <{SMTP_USER}>"
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
