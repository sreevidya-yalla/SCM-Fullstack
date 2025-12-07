from fastapi_mail import FastMail, MessageSchema
from app.config import conf

async def send_email(subject, recipient, body):
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype="plain"
    )
    fm = FastMail(conf)
    await fm.send_message(message)
