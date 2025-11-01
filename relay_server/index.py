#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pip install flask authlib flask-wtf requests
"""

from flask import (Flask, g, render_template, request, flash, redirect, make_response, Response,
                   send_from_directory, abort, url_for as flask_url_for)
import time
import json
import sys
import os
import database
import helper
from authlib.integrations.flask_client import OAuth
import logging
from logging.handlers import RotatingFileHandler
import settings
from datetime import datetime, timezone
from flask_wtf import CSRFProtect
from flask import jsonify
from werkzeug.utils import secure_filename


sys.path.insert(0, os.path.dirname(__file__))

UPLOAD_FOLDER = "firmware"
ALLOWED_EXTENSIONS = ["bin"]

application = Flask(__name__, static_url_path='/static', static_folder='static')
application.config['SECRET_KEY'] = settings.APP_SECRET_KEY
application.config['SESSION_COOKIE_NAME'] = 'gate_ctrl'
application.config['WTF_CSRF_SECRET_KEY'] = application.config['SECRET_KEY']
application.config['APPLICATION_ROOT'] = '/'
application.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

file_handler = RotatingFileHandler(os.path.join(database.temp_dir, "app.log"), maxBytes=65535, backupCount=1)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt='%Y-%m-%dT%H:%M:%S'
)
file_handler.setFormatter(formatter)
# Always include file handler
handlers = [file_handler]
# If running in debug mode, also add console logs
if application.debug:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
logging.basicConfig(level=logging.DEBUG, handlers=handlers)

logger = logging.getLogger(__name__)

csrf = CSRFProtect(application)

CLIENT_SECRETS_FILE = "client_secret.json"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if application.debug:
    google = None
else:
    if os.path.isfile(CLIENT_SECRETS_FILE):
        with open(CLIENT_SECRETS_FILE) as f:
            client_secrets = json.load(f)['web']  # Assumes the JSON structure is under 'web'

        # Configure OAuth
        oauth = OAuth(application)

        google = oauth.register(
            name='google',
            client_id=client_secrets['client_id'],
            client_secret=client_secrets['client_secret'],
            access_token_url=client_secrets['token_uri'],
            access_token_params=None,
            authorize_url=client_secrets['auth_uri'],
            authorize_params=None,
            api_base_url='https://www.googleapis.com/oauth2/v1/',
            userinfo_endpoint='https://www.googleapis.com/oauth2/v3/userinfo',
            client_kwargs={'scope': 'email'},
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
        )

'''
On a CGI hosting, the flasks url_for populates the url with script path,
so you get junk data that does not resolve to a valid url. This is an override to clean it up.
'''
def safe_url_for(endpoint, **values):

    url = flask_url_for(endpoint, **values)
    script_name = request.environ.get('SCRIPT_NAME', '')
    if script_name and url.startswith(script_name):
        url = url[len(script_name):] or '/'
    return url


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_connected_devices_for_index(connection):
    connected_devices = []

    main_device = database.get_device(connection=connection, name="main")

    if main_device:
        devices = [main_device]
    else:
        devices = database.get_device(connection=connection, authorized=1)

    if devices:
        for device in devices:
            # Special rule: If this is the main device, always show it
            if device["name"] == "main":
                dev_data = device.get("data")
                dev_label = dev_data.get("label", device["name"])
                sw_count = dev_data.get("sw_count", 1)
                restarted_at = device.get("restarted_at", "")
                reset_at = dev_data.get("reset_at", settings.RESET_DEVS_AT)
                connected_devices.append({
                    "name": device["name"],
                    "sw_count": sw_count,
                    "label": dev_label,
                    "restarted_at": restarted_at,
                    "reset_at": reset_at
                })
            else:
                ping_at = device.get("ping_at")
                if ping_at and ping_at != "None":
                    try:
                        ping_time = helper.iso_to_epoch(ping_at)
                    except Exception:
                        ping_time = 0
                    dev_connected = (time.time() - ping_time) < settings.LIFESIGN_TIMEOUT
                    if dev_connected:
                        dev_data = device.get("data")
                        dev_label = dev_data.get("label", device["name"])
                        sw_count = dev_data.get("sw_count", 1)
                        restarted_at = device.get("restarted_at", "")
                        reset_at = dev_data.get("reset_at", settings.RESET_DEVS_AT)
                        connected_devices.append({
                            "name": device["name"],
                            "sw_count": sw_count,
                            "label": dev_label,
                            "restarted_at": restarted_at,
                            "reset_at": reset_at
                        })

    return connected_devices


@application.before_request
def before_request():
    g.db = database.open_db()


@application.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        database.close_db(g.db)


@application.route('/authorize')
def authorize():
    auth_url = safe_url_for('oauth2callback')
    return google.authorize_redirect(f"https://{request.host}{auth_url}")


@application.route('/login', methods=['GET'])
def login():
    if application.debug:
        token = helper.generate_token()
        user_email = "local@localhost"
        user = database.get_user(connection=g.db, email=user_email)
        if not user:
            database.add_user(connection=g.db, email=user_email, apartment='0', token=token )
            user = database.get_user(connection=g.db, email=user_email)
        database.update_user(connection=g.db, email=user_email, token=token, authorized=2)

        response = make_response(redirect(safe_url_for('index')))
        response.set_cookie('token', token, max_age=settings.MAX_COOKIE_AGE, expires=time.time() + settings.MAX_COOKIE_AGE)
        return response

    return render_template('signin.html', title=settings.APP_TITLE, url_for=safe_url_for)


@application.route('/oauth2callback')
def oauth2callback():
    global google

    if application.debug:
        # Just redirect to index, since login is automatic in /login for debug
        return redirect(safe_url_for('index'))

    try:
        google.authorize_access_token()
        resp = google.get('userinfo')
        user_info = resp.json()
        email = user_info["email"]
        picture = user_info.get("picture")

        token = helper.generate_token()

        user = database.get_user(connection=g.db, email=email)
        if not user:
            if settings.APARTMENT_BUILDING_MODE:
                # Ask user to enter apartment number
                return redirect(safe_url_for('complete_registration', email=email))
            else:
                # Add as pending with default values
                database.add_user(connection=g.db, email=email, token=token, apartment="?")
                user = database.get_user(connection=g.db, email=email)

        database.update_user(connection=g.db, email=email, token=token, picture=picture)

        if user.get("authorized") > 0:
            response = make_response(redirect(safe_url_for('index')))
            response.set_cookie('token', token, max_age=settings.MAX_COOKIE_AGE, expires=time.time() + settings.MAX_COOKIE_AGE)
        else:
            flash("Your account has not been authorized yet.")
            response = redirect(safe_url_for("login"))
            response.set_cookie('token', 'None', expires=0)

    except Exception as e:
        logger.exception(f"OAuth2 callback error {e}")
        # Restart the login flow
        google = oauth.register(
            name='google',
            client_id=client_secrets['client_id'],
            client_secret=client_secrets['client_secret'],
            access_token_url=client_secrets['token_uri'],
            access_token_params=None,
            authorize_url=client_secrets['auth_uri'],
            authorize_params=None,
            api_base_url='https://www.googleapis.com/oauth2/v1/',
            userinfo_endpoint='https://www.googleapis.com/oauth2/v3/userinfo',
            client_kwargs={'scope': 'email'},
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
        )

        response = redirect(safe_url_for("login"))
        response.set_cookie('token', 'None', expires=0)

    return response


@application.route('/', methods=['GET'])
def index():
    token = request.cookies.get('token')
    if not token:
        return redirect(safe_url_for('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user:
        return redirect(safe_url_for('login'))

    connected_devices = get_connected_devices_for_index(g.db)

    unauthorized_users = database.get_user(connection=g.db, authorized=0)
    return render_template('home.html',
                           connected_devices=connected_devices,
                           admin=user.get("authorized", 0) > 1,
                           unauthorized_users=unauthorized_users,
                           user=user,
                           title=settings.APP_TITLE,
                           url_for=safe_url_for)


@application.route('/device_report', methods=['GET'])
def device_report():
    args = request.args
    name = args.get("name")

    if not name:
        return "Missing 'name' parameter", 400

    current_timestamp = int(time.time())
    relay_device = database.get_device(connection=g.db, name=name)
    if not relay_device:
        unauthorized_devs = database.get_device(connection=g.db, authorized=0)

        if len(unauthorized_devs) < 2:
            database.add_device(connection=g.db, name=name, ping_at=current_timestamp)
            return "Unauthorized", 401
        else:
            return "Unauthorized (Too many)", 401

    authorized = relay_device["authorized"]
    if authorized < 1:
        database.update_device(
            connection=g.db,
            name=name,
            ping_at=current_timestamp
        )
        return "Unauthorized", 401

    restarted_at_iso = relay_device.get("restarted_at")
    if restarted_at_iso and restarted_at_iso != "None":
        try:
            restarted_at_epoch = helper.iso_to_epoch(restarted_at_iso)
        except Exception:
            restarted_at_epoch = 0
    else:
        restarted_at_epoch = 0

    do_restart_flag = False
    response = "OK"
    dev_data = relay_device.get("data")
    dev_command = relay_device.get("command")
    if dev_data:
        if (current_timestamp - restarted_at_epoch) > (2 * 60 * 60):
            target_reset_hour = int(dev_data.get("reset_at", settings.RESET_DEVS_AT))
            utc_now = datetime.now(timezone.utc)
            if utc_now.hour == target_reset_hour:
                # time to restart the device
                response = json.dumps({
                    "command": "restart"
                })
                restarted_at_epoch = current_timestamp
                do_restart_flag = True

    # Process pending commands
    if not do_restart_flag and dev_command:
        # Firmware update command
        update_at = dev_command.get("update_at")
        firmware_id = dev_command.get("firmware_id")

        if update_at and firmware_id:
            # Only act on update if issued recently
            if 0 <= current_timestamp - int(update_at) < (settings.LIFESIGN_TIMEOUT * 2):
                response = json.dumps({
                    "command": "update",
                    "firmware": f"/firmware/{firmware_id}"
                })
        else:
            # Unlock command
            unlock_epoch_time = dev_command.get("unlocked_at", 0)
            unlock_interval = current_timestamp - unlock_epoch_time
            if 0 < unlock_interval < (settings.LIFESIGN_TIMEOUT * 2):
                response = json.dumps({
                    "relay_id": dev_command.get("relay_id", 0),
                    "command": "unlock"
                })

        # mark command as handled
        database.update_device(connection=g.db, name=name, command=None)

    # Save ping and restart time as ISO
    database.update_device(
        connection=g.db,
        name=name,
        ping_at=current_timestamp,
        restarted_at=restarted_at_epoch
    )

    return response, 200


@application.route('/unlock', methods=['GET'])
def unlock():
    args = request.args
    relay_index = args.get("id")
    device_name = args.get("name")

    token = request.cookies.get('token')
    if not token:
        return jsonify({"error": "unauthorized"}), 401

    if not device_name:
        return redirect(safe_url_for('index'))

    user = database.get_user(connection=g.db, token=token)
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    main_device = database.get_device(connection=g.db, name="main")
    if main_device:
        # Get all authorized devices
        connected_devices = database.get_device(connection=g.db, authorized=1)
    else:
        # Get only the requested device
        connected_devices = [database.get_device(connection=g.db, authorized=1, name=device_name)]

    if connected_devices:
        dev_found = False
        for device in connected_devices:
            if device["name"] != "main":
                current_timestamp = int(time.time())
                command = json.dumps({
                    "unlocked_at": current_timestamp,
                    "relay_id": relay_index
                })
                database.update_device(connection=g.db, name=device["name"], command=command)
                dev_found = True

        if dev_found:
            return jsonify({"status": "ok"}), 200

    return jsonify({"error": "device not found"}), 404


@application.route('/manage_users', methods=['GET'])
def manage_users():
    token = request.cookies.get('token')
    if not token:
        return redirect(safe_url_for('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user:
        return redirect(safe_url_for('login'))
    elif user["authorized"] < 2:
        flash("You are not authorized to authorize users.")
        return redirect(safe_url_for('index'))

    unauthorized_users = database.get_user(connection=g.db, authorized=0)

    authorized_users = (
        database.get_user(connection=g.db, authorized=1)
        + database.get_user(connection=g.db, authorized=2)
    )

    # ✅ Sort: put current user last, others alphabetical by email
    authorized_users_sorted = sorted(
        authorized_users,
        key=lambda u: (u["email"].lower() == user["email"].lower(), u["email"].lower())
    )

    # ✅ Sort unauthorized users too, if you want
    unauthorized_users_sorted = sorted(
        unauthorized_users,
        key=lambda u: u["email"].lower()
    )

    return render_template(
        'manage_users.html',
        unauthorized_users=unauthorized_users_sorted,
        authorized_users=authorized_users_sorted,
        user=user,
        title=settings.APP_TITLE,
        url_for=safe_url_for,
        apartment_building_mode=settings.APARTMENT_BUILDING_MODE
    )


@application.route('/manage_users', methods=['POST'])
def manage_users_post():
    token = request.cookies.get('token')
    if not token:
        return redirect(safe_url_for('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user or user["authorized"] < 2:
        flash("You are not authorized to perform this action.")
        return redirect(safe_url_for('index'))

    email = request.form.get('email')
    action = request.form.get('action')
    make_admin = request.form.get('make_admin')

    if not email or not action:
        return redirect(safe_url_for('manage_users'))

    if action == 'authorize':
        level = 2 if make_admin else 1
        database.update_user(connection=g.db, email=email, authorized=level)

    elif action == 'remove':
        database.delete_user(connection=g.db, email=email)

    elif action == 'make_admin':
        database.update_user(connection=g.db, email=email, authorized=2)

    elif action == 'update_apartment':
        apartment = request.form.get('apartment')
        if apartment:
            database.update_user(connection=g.db, email=email, apartment=apartment)

    database.sync_temp_db_to_disk(connection=g.db)

    return redirect(safe_url_for('manage_users'))


@application.route('/approve_user', methods=['GET'])
def approve_user():
    email = request.args.get('email')
    token = request.args.get('token')

    if not email or not token:
        return "Invalid request.", 400

    user = database.get_user(connection=g.db, email=email)
    if not user:
        return "User not found.", 404

    # Validate token matches
    if user.get('token') != token:
        return "Invalid or expired approval token.", 403

    # Approve and clear token — optional
    database.update_user(connection=g.db, email=email, authorized=1, token=None)

    body = (f"Your application for {settings.APP_TITLE} has been approved.\n "
            f"You may now access {request.host_url}")

    helper.send_email(
        recipient=email,
        subject=f"{settings.APP_TITLE} registration approved",
        body=body
    )

    database.sync_temp_db_to_disk(connection=g.db)

    return f"✅ User {email} has been approved and email sent as confirmation! They can now log in."


@application.route('/complete_registration', methods=['GET', 'POST'])
def complete_registration():
    if request.method == 'GET':
        email = request.args.get('email')

        if not email:
            return "Missing email", 400

        return render_template(
            'complete_registration.html',
            email=email,
            title="Complete Registration",
            url_for=safe_url_for
        )

    else:
        email = request.form.get('email')
        apartment = request.form.get('apartment')
        comment = request.form.get('comment') or ''

        if not email or not apartment:
            flash("Missing details")
            return redirect(request.url)

        # Generate approval token
        approval_token = helper.generate_token()
        database.add_user(connection=g.db, email=email, token=approval_token, apartment=apartment)

        # Notify admins
        admins = database.get_user(connection=g.db, authorized=2)
        for admin in admins:
            approve_link = f"{request.host_url}approve_user?email={email}&token={approval_token}"
            body = (
                f"New user: {email}\n"
                f"Apartment: {apartment}\n"
                f"Comment: {comment}\n\n"
                f"Approve directly: {approve_link}\n"
                f"Or manage here: {request.host_url.rstrip('/')}{safe_url_for('manage_users')}"
            )

            helper.send_email(
                recipient=admin.get('email'),
                subject=f"New user sign up at {settings.APP_TITLE}",
                body=body
            )

        database.sync_temp_db_to_disk(connection=g.db)
        flash("Registration submitted! You will receive an email when an administrator approves it")
        return redirect(safe_url_for('login'))


@application.route('/export_emails')
def export_emails():
    # Collect all emails
    all_users = database.get_user(connection=g.db)
    emails = [u.get('email') for u in all_users]

    # Create a CSV-like string
    csv_content = ", ".join(emails)

    # Send as a downloadable file
    return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=email.txt"}
    )


@application.route('/manage_devices', methods=['GET'])
def manage_devices():
    token = request.cookies.get('token')
    if not token:
        return redirect(safe_url_for('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user or user['authorized'] < 2:
        flash('You are not authorized to authorize devices.')
        return redirect(safe_url_for('index'))

    try:
        main_device = database.get_device(connection=g.db, name="main")
        single_device_mode = bool(main_device)
    except Exception as e:
        logger.error(f"Error checking device mode: {e}")
        single_device_mode = False  # fallback

    authorized_devices = database.get_device(g.db, authorized=1)
    unauthorized_devices = database.get_device(g.db, authorized=0)

    # Sort: "main" first, then the rest
    authorized_devices = sorted(
        authorized_devices,
        key=lambda d: 0 if d['name'] == 'main' else 1
    )

    # Collect firmware files to display
    firmware_files = []
    if os.path.exists(UPLOAD_FOLDER):
        firmware_files = sorted(os.listdir(UPLOAD_FOLDER), reverse=True)

    return render_template(
        'manage_devices.html',
        authorized_devices=authorized_devices,
        unauthorized_devices=unauthorized_devices,
        single_device_mode=single_device_mode,
        user=user,
        title=settings.APP_TITLE,
        url_for=safe_url_for,
        firmware_files=firmware_files
    )


@application.route('/manage_devices', methods=['POST'])
def manage_devices_post():
    token = request.cookies.get('token')
    if not token:
        return redirect(safe_url_for('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user or user['authorized'] < 2:
        flash("You are not authorized to manage devices.")
        return redirect(safe_url_for('index'))

    action = request.form.get('action')

    if action == 'authorize':
        name = request.form.get('device_name')
        database.update_device(connection=g.db, name=name, authorized=1)

    elif action == 'remove':
        name = request.form.get('device_name')
        database.delete_device(connection=g.db, name=name)

    elif action == 'update_single':
        name = request.form.get('device_name')
        label = request.form.get(f'{name}_label')
        sw_count = request.form.get(f'{name}_sw_count')
        reset_at = request.form.get(f'{name}_reset_at')

        try:
            sw_count = int(sw_count)
        except ValueError:
            sw_count = 1

        try:
            reset_at = int(reset_at)
        except ValueError:
            reset_at = settings.RESET_DEVS_AT

        # --- NEW: collect relay mappings for each button ---
        buttons = []
        for i in range(1, sw_count + 1):
            relay_val = request.form.get(f'{name}_relay_for_button_{i}')
            try:
                relay_id = int(relay_val)
            except (TypeError, ValueError):
                relay_id = i  # default 1→1, 2→2, etc.
            buttons.append({"id": i, "relay_id": relay_id})

        dev_data = {
            "label": label,
            "sw_count": sw_count,
            "reset_at": reset_at,
            "buttons": buttons
        }

        database.update_device(connection=g.db, name=name, data=dev_data)
        flash(f"Device '{name}' updated!")

    database.sync_temp_db_to_disk(connection=g.db)
    return redirect(safe_url_for('manage_devices'))


@application.route('/toggle_device_mode', methods=['POST'])
def toggle_device_mode():
    mode = request.form.get('mode')

    try:
        if mode == 'single':
            if not database.get_device(g.db, name="main"):
                database.add_device(g.db, "main")
                database.update_device(g.db, name="main", authorized=1)
        else:
            database.delete_device(g.db, "main")
    except Exception as e:
        logger.error(f"Failed to toggle device mode: {e}")
        flash("Could not toggle device mode. Check server logs and database permissions.")

    database.sync_temp_db_to_disk(connection=g.db)
    return redirect(safe_url_for('manage_devices'))


@application.route("/upload_firmware", methods=["POST"])
def upload_firmware():
    if "firmware_file" not in request.files:
        flash("No file part")
        return redirect(safe_url_for("manage_devices"))

    file = request.files["firmware_file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(safe_url_for("manage_devices"))

    if file and allowed_file(file.filename):
        original_name = secure_filename(file.filename)

        # prepend timestamp (e.g. 2025-10-18_19-31-45_filename.bin)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{timestamp}_{original_name}"

        filepath = os.path.join(application.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        flash(f"Firmware '{original_name}' uploaded as '{filename}'.")
        return redirect(safe_url_for("manage_devices"))

    flash(f"Invalid file type. Only {ALLOWED_EXTENSIONS} allowed.")
    return redirect(safe_url_for("manage_devices"))


@application.route("/delete_firmware", methods=["POST"])
def delete_firmware():
    filename = request.form.get("filename")
    if not filename:
        flash("Missing filename.")
        return redirect(safe_url_for("manage_devices"))

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f"Firmware '{filename}' deleted.")
    else:
        flash("File not found.")

    return redirect(safe_url_for("manage_devices"))

@application.route("/start_update", methods=["POST"])
def start_update():
    firmware = request.form.get("firmware")
    selected_devices = request.form.getlist("devices")

    current_timestamp = int(time.time())

    for device in selected_devices:
        command = json.dumps({
            "update_at": current_timestamp,
            "firmware_id": firmware
        })
        database.update_device(connection=g.db, name=device, command=command)

    flash(f"Started update of {firmware} on {len(selected_devices)} devices.")
    return redirect(safe_url_for("manage_devices"))


@application.route("/firmware/<filename>")
def download_firmware(filename):
    upload_folder = application.config["UPLOAD_FOLDER"]
    safe_name = secure_filename(filename)
    filepath = os.path.join(upload_folder, safe_name)

    if not os.path.exists(filepath):
        abort(404)

    # Send the file with correct MIME type
    return send_from_directory(upload_folder, safe_name, as_attachment=True, mimetype="application/octet-stream")


if __name__ == "__main__":
    database.setup_initial_db()
    application.run(debug=True, host="0.0.0.0", port=5000)


