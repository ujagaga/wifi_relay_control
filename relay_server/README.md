# Gate Server

Python3 Flask website to control WiFi relay devices

Once you create the hardware devices, they will try to access the website. Their ID will be added to device database, 
but only the last 2 unauthorized devices.
You will need to run: ```device_edit.py``` to enable them. 

The user login is done using Google OAuth2, so the user emails must be GMail based. The upside is there is no password.
After the first user logs in, run ```user_edit.py``` to authorize it as an admin. 
After this the admin will be able to authorize other users via website.
