import string
import random
from hashlib import sha256
import sys
import settings
from datetime import datetime, timezone
import paho.mqtt.client as mqtt
import threading
import paho.mqtt.publish as publish
import logging

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


def publish_mqtt_message(message):
    def worker():
        publish.single(
            topic=settings.MQTT_TOPIC,
            payload=message,
            hostname=settings.MQTT_BROKER,
            port=settings.MQTT_PORT,
            auth={
                'username': settings.MQTT_USER,
                'password': settings.MQTT_PASS
            },
            keepalive=60
        )
        logger.info(f"Published MQTT message: {message}")

    threading.Thread(target=worker).start()


def iso_to_epoch(iso_str: str) -> int:
    dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    return int(dt.timestamp())


def epoch_to_iso(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
