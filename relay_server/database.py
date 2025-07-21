import sys
import sqlite3
import settings
import json
import helper
import logging

logger = logging.getLogger(__name__)

def check_table_exists(connection, tablename):
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (tablename,))
    data = cursor.fetchone()
    result = bool(data)
    cursor.close()
    return result


def init_database(connection):
    cursor = connection.cursor()

    if not check_table_exists(connection, "users"):
        sql = """
        CREATE TABLE users (
            email TEXT NOT NULL UNIQUE,
            token TEXT UNIQUE,
            picture TEXT,
            authorized INTEGER DEFAULT 0
        );
        """
        cursor.execute(sql)
        connection.commit()

    if not check_table_exists(connection, "devices"):
        sql = """
        CREATE TABLE devices (
            name TEXT NOT NULL UNIQUE,
            ping_at TEXT,
            data TEXT,
            authorized INTEGER DEFAULT 0,
            restarted_at TEXT
        );
        """
        cursor.execute(sql)
        connection.commit()

    cursor.close()


def open_db():
    connection = sqlite3.connect(settings.DB_NAME)
    connection.row_factory = sqlite3.Row  # So we can use row["colname"]
    return connection


def close_db(connection):
    connection.close()


def add_user(connection, email: str):
    sql = "INSERT INTO users (email) VALUES (?);"

    try:
        connection.execute(sql, (email,))
        connection.commit()
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.exception(f"ERROR adding user to db on line {exc_tb.tb_lineno}!\n\t{exc}")


def delete_user(connection, email: str):
    sql = "DELETE FROM users WHERE email = ?;"

    try:
        connection.execute(sql, (email,))
        connection.commit()
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.exception(f"ERROR adding user to db on line {exc_tb.tb_lineno}!\n\t{exc}")


def get_user(connection, email: str = None, token: str = None, authorized: int = None):
    one = True
    if email:
        sql = "SELECT * FROM users WHERE email = ?;"
        params = (email,)
    elif token:
        sql = "SELECT * FROM users WHERE token = ?;"
        params = (token,)
    elif authorized is not None:
        sql = "SELECT * FROM users WHERE authorized = ?;"
        params = (authorized,)
        one = False
    else:
        sql = "SELECT * FROM users;"
        params = ()
        one = False

    user = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        if one:
            row = cursor.fetchone()
            user = dict(row) if row else None

            # ✅ Ensure default picture for single user
            if user and not user.get("picture"):
                user["picture"] = "/static/blank_user.png"

        else:
            rows = cursor.fetchall()
            user = []
            for r in rows:
                row_dict = dict(r)
                if not row_dict.get("picture"):
                    row_dict["picture"] = "/static/blank_user.png"
                user.append(row_dict)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.exception(f"ERROR adding user to db on line {exc_tb.tb_lineno}!\n\t{exc}")
        if "no such table" in f"{exc}":
            # Try to initialize the database
            init_database(connection)
    return user



def update_user(connection, email: str, token: str = None, authorized: int = None, picture:str = None):
    user = get_user(connection, email=email)

    if user:
        if token is not None:
            user["token"] = token
        if authorized is not None:
            user["authorized"] = authorized
        if picture is not None:
            user["picture"] = picture

        sql = "UPDATE users SET token = ?, authorized = ?, picture = ? WHERE email = ?;"
        params = (user["token"], user["authorized"], user["picture"], email)

        try:
            connection.execute(sql, params)
            connection.commit()
        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.exception(f"ERROR adding user to db on line {exc_tb.tb_lineno}!\n\t{exc}")


def add_device(connection, name: str, ping_at: int = None):
    ping_at_iso = helper.epoch_to_iso(ping_at) if ping_at else None

    sql = "INSERT INTO devices (name, ping_at) VALUES (?, ?);"

    try:
        connection.execute(sql, (name, ping_at_iso))
        connection.commit()
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.exception(f"ERROR adding device to db on line {exc_tb.tb_lineno}!\n\t{exc}")



def get_device(connection, name: str = None, authorized: int = None):
    one = True
    if name:
        sql = "SELECT * FROM devices WHERE name = ?;"
        params = (name,)
    elif authorized is not None:
        sql = "SELECT * FROM devices WHERE authorized = ?;"
        params = (authorized,)
        one = False
    else:
        sql = "SELECT * FROM devices;"
        params = ()
        one = False

    device = None
    try:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        if one:
            row = cursor.fetchone()
            if row:
                device = dict(row)
                if device.get("data"):
                    try:
                        device["data"] = json.loads(device["data"])
                    except json.JSONDecodeError:
                        device["data"] = {}
                else:
                    device["data"] = {}

                if not device.get("restarted_at"):
                    device["restarted_at"] = 0
            else:
                device = None
        else:
            rows = cursor.fetchall()
            device = []
            for r in rows:
                d = dict(r)
                if d.get("data"):
                    try:
                        d["data"] = json.loads(d["data"])
                    except json.JSONDecodeError:
                        d["data"] = {}

                if not d.get("restarted_at"):
                    d["restarted_at"] = 0
                device.append(d)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.exception(f"ERROR adding user to db on line {exc_tb.tb_lineno}!\n\t{exc}")

    return device


def update_device(
    connection, name: str,
    ping_at: int = None,
    authorized: int = None,
    restarted_at: int = None,
    data=None  # accept str or dict
):
    device = get_device(connection, name=name)

    if device:
        if ping_at is not None:
            device["ping_at"] = helper.epoch_to_iso(ping_at)
        if restarted_at is not None:
            device["restarted_at"] = helper.epoch_to_iso(restarted_at)
        if authorized is not None:
            device["authorized"] = authorized
        if data is not None:
            device["data"] = data

        if isinstance(device.get("data"), dict):
            device["data"] = json.dumps(device.get("data"))

        sql = """
        UPDATE devices
        SET ping_at = ?, restarted_at = ?, authorized = ?, data = ?
        WHERE name = ?;
        """
        params = (
            device.get("ping_at"),
            device.get("restarted_at"),
            device.get("authorized"),
            device.get("data"),
            name
        )

        try:
            connection.execute(sql, params)
            connection.commit()
        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.exception(f"ERROR adding user to db on line {exc_tb.tb_lineno}!\n\t{exc}")


def delete_device(connection, name: str):
    sql = "DELETE FROM devices WHERE name = ?;"

    try:
        connection.execute(sql, (name,))
        connection.commit()
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.exception(f"ERROR adding user to db on line {exc_tb.tb_lineno}!\n\t{exc}")
