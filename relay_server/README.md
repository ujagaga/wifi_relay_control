# Relay Server

Python3 Flask website to control WiFi relay devices

The user login is done using Google OAuth2, so the user emails must be GMail based. The upside is there is no password.

Once you create the hardware devices, they will try to access the website. Their ID will be added to device database, 
but only the last 2 unauthorized devices.
An administrator will need to authorize each of them via website.

# How to start
You might need to create a virtual python environment and install python libraries: 

	pip install flask authlib flask-wtf requests gunicorn paho-mqtt

This can be done automatically by running the `install.sh`. Before you do, make a copy of the `settings.py.example` 
and rename it to `settings.py`. Then adjust the info in it according to your needs. 

Deploy this on a Raspberry Pi, dedicated hosting, Oracle cloud instance or any other computer. 
If you deploy on a local computer, you will need to make a reverse HTTP tunnel or provide a public IP.
You can use a Cloudflare tunnel, NGrok or any similar service, just make sure to disable caching as 
the devices will need to be notified of every change to be able to respond to commands. 

Note that CGI based hosting will not work without an mqtt server due to caching and DDOS attack policies. The devices would need to ping the server every 2s, 
which the CGI based server will prevent. You can increase the ping time to maybe 30s, but then you need an mqtt server for devices to receive commands to not wait 30s for a response. If you do use a dedicated hosting and an MQTT server, keep in mind that most providers allow outbound traffic at ports 80, 433 and above 49000, so you would need to use an MQTT server at port higher than 49000.

If you run this on your local machine a local user will be created and you can just use it. A reverse tunnel should 
provide its own ssl certificate, to support https. This is necessary to allow Google OAUTH2 authentication. 
To enable this, you need to create an application on Google Cloud Console, activate OAuth2 API and download client secrets file.
Paste the "client secrets file" into the `relay_server` folder.
The simplest way to enable multiple users without having to configure them in developer console is to not upload a logo
and just publish the app.

## Note
- The port on which it will run is 5000. It is set in the `run_server.sh` which is activated by the service on startup.
- The admin email is set in the `settings.py` and automatically enabled. All other users can be enabled by the admin after the first login attempt.
- The SQLite database will be located in the `relay_server` folder, but at startup it will be copied to `/dev/shm/`.
 This is the shared memory space in RAM and will prevent storage wear on a raspberry Pi SD card due to frequent write. When you save any settings from UI, 
 the temporary database in shared memory will be copied over the main database to persist the changes

 
