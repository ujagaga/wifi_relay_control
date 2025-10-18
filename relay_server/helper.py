import string
import random
from hashlib import sha256
import sys
import settings
from datetime import datetime, timezone
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

logger = logging.getLogger(__name__)
DATE_FORMAT = "%Y-%m-%d"


def generate_token():
    return ''.join(random.choices(string.ascii_letters, k=32))


def hash_password(password: str):
    return sha256(password.encode('utf-8')).hexdigest()


def generate_random_string():
    return hash_password(generate_token())


def string_to_date(valid_until: str):
    result = None

    try:
        result = datetime.strptime(valid_until, DATE_FORMAT)
        # Setting to middle of the day for easier comparison.
        result = result.replace(hour=12, minute=0)
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.error("ERROR converting string to date on line {}!\n\t{}".format(exc_tb.tb_lineno, exc))

    return result


def date_to_string(valid_date: datetime) -> str:
    return valid_date.strftime(DATE_FORMAT)


def to_int(number, default = 0):
    try:
        return int(number)
    except:
        return default


def iso_to_epoch(iso_str: str) -> int:
    dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    return int(dt.timestamp())


def epoch_to_iso(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def rough_time_ago(seconds_ago: int) -> str:
    minutes = seconds_ago // 60
    hours = minutes // 60
    days = hours // 24

    if hours < 24:
        return "today"
    elif days == 1:
        return "yesterday"
    elif days < 7:
        return f"{days} days ago"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    elif days < 365:
        months = days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        return "more than a year ago"


'''
Sends an email using configured credentials. 
'''
def send_email(recipient, subject, body):
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_USER
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        logger.info(f"Sending email to: {recipient}")
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.ehlo()
            # Add if needed:
            # server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(settings.SMTP_USER, recipient, msg.as_string())
            logger.info("Sending email done")

    except Exception as e:
        logger.exception(f"Error sending email: {e}")


