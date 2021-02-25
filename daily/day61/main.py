import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


logger = logging.getLogger(__name__)

message = Mail(
    from_email="usjoeylou@gmail.com",
    to_emails="richardlou99@gmail.com",
    subject="Sending with Twilio SendGrid is Fun",
    html_content="<strong>and easy to do anywhere, even with Python</strong>",
)
try:
    sg = SendGridAPIClient(
        "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"
    )
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)
except Exception as e:
    print(e.message)
