#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import database


def list_devices(connection, name: str = None):
    devices = database.get_device(connection, name=name)

    message = "INFO: Listing devices in database"

    if name:
        print(f'{message} with name "{name}":')
        if devices:
            print("\t", devices)
        else:
            print("\tINFO: No device found with specified name!")
    else:
        print(f'{message}:')
        if len(devices) == 0:
            print("\tINFO: No devices found in database.")
        else:
            for device_obj in devices:
                print("\t", device_obj)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", help="List devices", required=False, action='store_true')
    parser.add_argument("-d", "--delete", help="Delete specified device", required=False, action='store_true')
    parser.add_argument("-a", "--authorize", help="Authorize device", required=False, action='store_true')
    parser.add_argument("-n", "--name", help="Specify device name", required=False)

    args = parser.parse_args()

    connection = database.open_db()

    database.init_database(connection)

    if args.list:
        list_devices(connection)

    elif args.delete:
        if args.name:
            print(f"INFO: Deleting device with name: {args.name}")
            database.delete_device(connection, name=args.name)

            print("Checking result:")
            list_devices(connection, name=args.name)
        else:
            print("ERROR: Please provide name of the device to delete.")

    elif args.authorize:
        if args.name:
            device = database.get_device(connection, name=args.name)
            if device:
                database.update_device(connection, name=args.name, authorized=1)
            else:
                print("ERROR: Specified device is not found in database.")
        else:
            print("ERROR: Please provide device name.")
    else:
        print("ERROR: No operation is specified.")
        parser.print_help()

    database.close_db(connection)
