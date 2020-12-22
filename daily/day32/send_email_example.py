import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tools.email_sender import GmailSender

APP_NAME = os.path.basename(__file__).replace(".py", "")
logger = logging.getLogger(APP_NAME)


def main():
    """ Read https://docs.python.org/3.5/library/email-examples.html for how to use MIME
    """
    to_addrs = "richardlou99@gmail.com"
    with GmailSender() as gsender:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Test"
        msg["To"] = to_addrs

        html = """\
        <html>
        <head></head>
        <body>
            <p>Hi!<br>
            How are you?<br>
            Here is the <a href="https://www.python.org">link</a> you wanted.
            </p>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))
        gsender.send([to_addrs], msg.as_string())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format=f"{APP_NAME}[%(levelname)s][%(asctime)s]: %(message)s",
    )
    main()
