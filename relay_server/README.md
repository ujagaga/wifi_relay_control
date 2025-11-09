# Relay Server

Python3 Flask website to control WiFi relay devices

The user login is done using Google OAuth2, so the user emails must be GMail based. The upside is there is no password.

Once you create the hardware devices, they will try to access the website. Their ID will be added to device database, 
but only the last 2 unauthorized devices.
An administrator will need to authorize each of them via website.

# How to start
You might need to create a virtual python environment and install python libraries: 

	pip install flask authlib flask-wtf requests gunicorn

This can be done automatically by running the `install.sh`. Before you do, make a copy of the `settings.py.example` 
and rename it to `settings.py`. Then adjust the info in it according to your needs. 

Deploy this on a Raspberry Pi or any other computer. Then you will need to make a reverse HTTP tunnel or provide a public IP.
I am using Cloudflare tunnel, but NGrok or any similar service will work too, just make sure to disable caching as 
the devices will need to be notified of every change to be able to respond to commands. 

A CGI based hosting will not work due to caching and DDOS attack policies. The devices will ping the server every 2s, 
which the CGI based server will prevent.

If you run this on your local machine a local user will be created and you can just use it. A reverse tunnel should 
provide its own ssl certificate, to support https. This is necessary to allow Google OAUTH2 authentication. 
To enable this, you need to create an application on Google Cloud Console, activate OAuth2 API and download client secrets file.
Paste the "client secrets file" into the `relay_server` folder.
The simplest way to enable multiple users without having to configure them in developer console is to not upload a logo
and just publish the app.

## Note
- The port on which it will run is 5000. It is set in the `run_server.sh` which is activated by the service on startup.
- The admin email is set in the `settings.py` and automatically enabled. All other users can be enabled by the admin after the first login attempt.
- The SQLite database will be located in the `relay_server` folder, but at startup, it will be copied to `/dev/shm/`.
 This is the shared memory space in RAM and will prevent storage wear due to frequent write. When you save any settings from UI, 
 the temporary database in shared memory will be copied over the main database to persist the changes

 
