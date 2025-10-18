import sys
import sqlite3
import settings
import json
import helper
import logging
import time
import os
import shutil


logger = logging.getLogger(__name__)
script_dir = os.path.dirname(os.path.abspath(__file__))
persist_db = os.path.join(script_dir, settings.DB_NAME)
temp_dir = os.path.join("/dev", "shm", settings.APP_TITLE)
temp_db = os.path.join(temp_dir, settings.DB_NAME)
os.makedirs(temp_dir, exist_ok=True)


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
               authorized INTEGER DEFAULT 0,
               apartment TEXT,
               last_seen TEXT
           );
           """
        cursor.execute(sql)
        connection.commit()

        # Insert super admin user here
        insert_sql = """
            INSERT INTO users (email, authorized)
            VALUES (?, ?)
        """
        cursor.execute(insert_sql, (settings.SUPER_ADMIN, 2))  # 1 = authorized as user, 2 = admin
        connection.commit()

    if not check_table_exists(connection, "devices"):
        sql = """
        CREATE TABLE devices (
            name TEXT NOT NULL UNIQUE,
            ping_at TEXT,
            data TEXT,
            authorized INTEGER DEFAULT 0,
            command TEXT,
            restarted_at TEXT
        );
        """
        cursor.execute(sql)
        connection.commit()

    cursor.close()


def open_db(db_path=temp_db):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def close_db(connection):
    connection.close()


def add_user(connection, email: str, token:str, apartment: str):
    sql = "INSERT OR REPLACE INTO users (email, token, apartment) VALUES (?, ?, ?);"

    try:
        connection.execute(sql, (email, token, apartment))
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

            if user:
                if not user.get("picture"):
                    user["picture"] = "/static/blank_user.png"
                # Update last_seen to now (ISO format)
                current_timestamp = helper.epoch_to_iso(int(time.time()))
                user["last_seen"] = current_timestamp
                connection.execute("UPDATE users SET last_seen = ? WHERE email = ?;",
                                   (current_timestamp, user["email"]))
                connection.commit()

        else:
            rows = cursor.fetchall()
            user = []
            for r in rows:
                row_dict = dict(r)
                if not row_dict.get("picture"):
                    row_dict["picture"] = "/static/blank_user.png"

                if row_dict.get("last_seen"):

                    try:
                        epoch = helper.iso_to_epoch(row_dict["last_seen"])
                        seconds_ago = int(time.time()) - epoch
                        row_dict["last_seen"] = helper.rough_time_ago(seconds_ago)
                    except:
                        row_dict["last_seen"] = "unknown"
                else:
                    row_dict["last_seen"] = "never"

                user.append(row_dict)

    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.exception(f"ERROR adding user to db on line {exc_tb.tb_lineno}!\n\t{exc}")
        if "no such table" in f"{exc}":
            # Try to initialize the database
            init_database(connection)
    return user


def update_user(connection, email: str, token: str = None, authorized: int = None, picture:str = None, apartment = None):
    user = get_user(connection, email=email)

    if user:
        if token is not None:
            user["token"] = token
        if authorized is not None:
            user["authorized"] = authorized
        if picture is not None:
            user["picture"] = picture
        if apartment is not None:
            user["apartment"] = apartment

        sql = "UPDATE users SET token = ?, authorized = ?, picture = ?, apartment = ? WHERE email = ?;"
        params = (user["token"], user["authorized"], user["picture"], user["apartment"], email)

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

                if device.get("command"):
                    try:
                        device["command"] = json.loads(device["command"])
                    except json.JSONDecodeError:
                        device["command"] = {}
                else:
                    device["command"] = {}

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

                if d.get("command"):
                    try:
                        d["command"] = json.loads(d["command"])
                    except json.JSONDecodeError:
                        d["command"] = {}

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
    command = None,
    data = None
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
        if command is not None:
            device["command"] = command

        if isinstance(device.get("data"), dict):
            device["data"] = json.dumps(device.get("data"))
        if isinstance(device.get("command"), dict):
            device["command"] = json.dumps(device.get("command"))

        sql = """
        UPDATE devices
        SET ping_at = ?, restarted_at = ?, authorized = ?, data = ?, command = ?
        WHERE name = ?;
        """
        params = (
            device.get("ping_at"),
            device.get("restarted_at"),
            device.get("authorized"),
            device.get("data"),
            device.get("command"),
            name
        )

        try:
            connection.execute(sql, params)
            connection.commit()
        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            logger.exception(f"ERROR updating db on line {exc_tb.tb_lineno}!\n\t{exc}")


def delete_device(connection, name: str):
    sql = "DELETE FROM devices WHERE name = ?;"

    try:
        connection.execute(sql, (name,))
        connection.commit()
    except Exception as exc:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        logger.exception(f"ERROR adding user to db on line {exc_tb.tb_lineno}!\n\t{exc}")


def setup_initial_db():
    if not os.path.isfile(persist_db):
        connection = open_db(persist_db)
        init_database(connection)
        close_db(connection)

    if not os.path.isfile(temp_db):
        shutil.copy2(persist_db, temp_db)
        
def sync_temp_db_to_disk(connection=None):
    if connection:
        close_db(connection)

    # atomic replace. Safer in case of power failure mid copying
    tmp_backup = persist_db + ".tmp"
    shutil.copy2(temp_db, tmp_backup)
    os.replace(tmp_backup, persist_db)


if __name__ == "__main__":
    setup_initial_db()
