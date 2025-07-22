#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
pip install flask authlib paho-mqtt flask-wtf requests
'''
from flask import Flask, g, render_template, request, flash, redirect, make_response, url_for
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


sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(handlers=[RotatingFileHandler(os.path.join(os.path.dirname(__file__),'app.log'), maxBytes=10000, backupCount=1)],
        level=logging.DEBUG,
        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt='%Y-%m-%dT%H:%M:%S')

logger = logging.getLogger(__name__)

application = Flask(__name__, static_url_path='/static', static_folder='static')
application.config['SECRET_KEY'] = settings.APP_SECRET_KEY
application.config['SESSION_COOKIE_NAME'] = 'gate_ctrl'
application.config['WTF_CSRF_SECRET_KEY'] = application.config['SECRET_KEY']
csrf = CSRFProtect(application)

CLIENT_SECRETS_FILE = "client_secret.json"
IS_LOCAL = False


if IS_LOCAL:
    google = None
else:
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


def get_url(endpoint):
    home_url = url_for('index')
    resolved_url = url_for(endpoint).replace(home_url, '/')

    return resolved_url


def get_connected_devices(connection):
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
    auth_url = get_url('oauth2callback')
    return google.authorize_redirect(f"https://{request.host}{auth_url}")


@application.route('/login', methods=['GET'])
def login():
    if IS_LOCAL:
        # Generate a fake authorized user token automatically
        token = helper.generate_token()
        # Here you might want to add or update a special local user in DB
        # For example:
        user_email = "local@localhost"
        user = database.get_user(connection=g.db, email=user_email)
        if not user:
            database.add_user(connection=g.db, email=user_email)
            user = database.get_user(connection=g.db, email=user_email)
        database.update_user(connection=g.db, email=user_email, token=token, authorized=2)

        response = make_response(redirect(get_url('index')))
        response.set_cookie('token', token, max_age=settings.MAX_COOKIE_AGE, expires=time.time() + settings.MAX_COOKIE_AGE)
        return response

    return render_template('login.html')


@application.route('/oauth2callback')
def oauth2callback():
    if IS_LOCAL:
        # Just redirect to index, since login is automatic in /login for local
        return redirect(get_url('index'))

    google.authorize_access_token()
    resp = google.get('userinfo')
    user_info = resp.json()
    email = user_info["email"]
    picture = user_info.get("picture")

    user = database.get_user(connection=g.db, email=email)

    unauthorized_users = database.get_user(connection=g.db, authorized=False)
    if not user and (not unauthorized_users or (unauthorized_users and len(unauthorized_users) < 50)):
        database.add_user(connection=g.db, email=email)
        user = database.get_user(connection=g.db, email=email)

    if not user or user['authorized'] < 1:
        flash('You are not authorized to access this app. Please contact the administrator: ujagaga@gmail.com')
        return redirect(get_url('login'))

    token = helper.generate_token()
    database.update_user(connection=g.db, email=email, token=token, picture=picture)

    response = make_response(redirect(get_url('index')))
    response.set_cookie('token', token, max_age=settings.MAX_COOKIE_AGE, expires=time.time() + settings.MAX_COOKIE_AGE)
    return response


@application.route('/', methods=['GET'])
def index():
    token = request.cookies.get('token')
    if not token:
        return redirect(get_url('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user:
        return redirect(get_url('login'))

    connected_devices = get_connected_devices(g.db)

    unauthorized_users = database.get_user(connection=g.db, authorized=0)
    return render_template('index.html',
                           connected_devices=connected_devices,
                           admin=user.get("authorized", 0) > 1,
                           unauthorized_users=unauthorized_users,
                           user=user)


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

    response = "OK"
    dev_data = relay_device.get("data")
    if dev_data:
        if (current_timestamp - restarted_at_epoch) > (2 * 60 * 60):
            target_reset_hour = int(dev_data.get("reset_at", settings.RESET_DEVS_AT))
            utc_now = datetime.now(timezone.utc)
            if utc_now.hour == target_reset_hour:
                # time to restart the device
                response = json.dumps({
                    "host": name,
                    "command": "restart"
                })
                helper.publish_mqtt_message(response)
                restarted_at_epoch = current_timestamp

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

    user = database.get_user(connection=g.db, token=token)
    if not user:
        return jsonify({"error": "unauthorized"}), 401

    main_device = database.get_device(connection=g.db, name="main")
    all_devices = database.get_device(connection=g.db)
    if all_devices:
        for device in all_devices:
            if device["name"] == device_name or main_device:
                mqtt_message = json.dumps({
                    "host": device["name"],
                    "command": "trigger",
                    "relay_id": relay_index
                })
                helper.publish_mqtt_message(mqtt_message)
                return jsonify({"status": "ok"}), 200

    return jsonify({"error": "device not found"}), 404


@application.route('/manage_users', methods=['GET'])
def manage_users():
    token = request.cookies.get('token')
    if not token:
        return redirect(get_url('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user:
        return redirect(get_url('login'))
    elif user["authorized"] < 2:
        flash("You are not authorized to authorize users.")
        return redirect(get_url('index'))

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
        user=user
    )



@application.route('/manage_users', methods=['POST'])
def manage_users_post():
    token = request.cookies.get('token')
    if not token:
        return redirect(get_url('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user or user["authorized"] < 2:
        flash("You are not authorized to perform this action.")
        return redirect(get_url('index'))

    email = request.form.get('email')
    action = request.form.get('action')
    make_admin = request.form.get('make_admin')

    if not email or not action:
        return redirect(url_for('manage_users'))

    if action == 'authorize':
        level = 2 if make_admin else 1
        database.update_user(connection=g.db, email=email, authorized=level)

    elif action == 'remove':
        database.delete_user(connection=g.db, email=email)

    elif action == 'make_admin':
        database.update_user(connection=g.db, email=email, authorized=2)

    return redirect(url_for('manage_users'))


@application.route('/manage_devices', methods=['GET'])
def manage_devices():
    token = request.cookies.get('token')
    if not token:
        return redirect(get_url('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user or user['authorized'] < 2:
        flash('You are not authorized to authorize devices.')
        return redirect(get_url('index'))

    main_device = database.get_device(connection=g.db, name="main")
    single_device_mode = bool(main_device)

    authorized_devices = database.get_device(g.db, authorized=1)
    unauthorized_devices = database.get_device(g.db, authorized=0)

    # Sort: "main" first, then the rest
    authorized_devices = sorted(
        authorized_devices,
        key=lambda d: 0 if d['name'] == 'main' else 1
    )

    return render_template(
        'manage_devices.html',
        authorized_devices=authorized_devices,
        unauthorized_devices=unauthorized_devices,
        single_device_mode=single_device_mode,
        user=user
    )



@application.route('/manage_devices', methods=['POST'])
def manage_devices_post():
    token = request.cookies.get('token')
    if not token:
        return redirect(get_url('login'))

    user = database.get_user(connection=g.db, token=token)
    if not user or user['authorized'] < 2:
        flash("You are not authorized to manage devices.")
        return redirect(get_url('index'))

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
        dev_data = {"label": label, "sw_count": sw_count, "reset_at": reset_at}
        database.update_device(connection=g.db, name=name, data=dev_data)
        flash(f"Device '{name}' updated!")

    return redirect(url_for('manage_devices'))


@application.route('/toggle_device_mode', methods=['POST'])
def toggle_device_mode():
    mode = request.form.get('mode')
    if mode == 'single':
        if not database.get_device(g.db, name="main"):
            database.add_device(g.db, "main")
            database.update_device(g.db, name="main", authorized=1)
    else:
        database.delete_device(g.db, "main")
    return redirect(url_for('manage_devices'))


if __name__ == "__main__":
    # Disable Google auth for local development as it will not work without https
    IS_LOCAL = True
    application.run(debug=True, host="0.0.0.0", port=5000)