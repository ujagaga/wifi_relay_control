# Relay Server

Python3 Flask website to control WiFi relay devices

The user login is done using Google OAuth2, so the user emails must be GMail based. The upside is there is no password.
After the first user logs in, run ```user_edit.py``` to authorize it as an admin. 
After this the admin will be able to authorize other users via website.

Once you create the hardware devices, they will try to access the website. Their ID will be added to device database, 
but only the last 2 unauthorized devices.
An administrator will need to authorize each of them via website.

# How to start
You might need to create a virtual python environment and install python libraries: 

	pip install flask authlib paho-mqtt flask-wtf requests

If you run the index.py on your local machine a local user will be created and you can just use it. If you deploy this
on a CGI based hosting, you will need to login using GMail. To enable this, you need to create an application on 
Google Developer Console, activate OAuth2 API and download client secrets file.
The simplest way to enable multiple users without having to configure them in developer console is to not upload a logo
and just publish the app.
