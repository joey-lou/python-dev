from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import URL, DataRequired, Email

from tools.consts import GRID_CREDS
from tools.email_sender import GmailSender, GridSender


class ContactForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])
    email = StringField("email", validators=[Email()])
    phone = StringField("phone")
    message = StringField("message")
    submit = SubmitField("Send Feedback")


class PostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

    def to_dict(self):
        return {
            "title": self.title.data,
            "subtitle": self.subtitle.data,
            "author": self.author.data,
            "img_url": self.img_url.data,
            "body": self.body.data,
        }


def make_email_html(form: ContactForm):
    return f"""\
        <html>
        <head></head>
        <body>
            <p>This is sent from {form.name.data}<br>
            Email: {form.email.data}<br>
            Phone: {form.phone.data}<br>
            Message: {form.message.data}
            </p>
        </body>
        </html>
        """


def send_email(form: ContactForm):
    with GmailSender() as gsender:
        # send to my own gmail account
        my_email = gsender.oauth2.username
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Blog Message from {form.name.data}"
        msg["To"] = my_email

        html = make_email_html(form)

        msg.attach(MIMEText(html, "html"))
        gsender.send([my_email], msg.as_string())


def send_email_with_grid(form: ContactForm):
    html = make_email_html(form)
    with GridSender.from_creds_file(GRID_CREDS) as gs:
        gs.send(None, f"Blog Message from {form.name.data}", html)
