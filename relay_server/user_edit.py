#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import database


def list_users(db_connection, email: str = None):
    users = database.get_user(db_connection, email=email)
    message = "INFO: Listing users in database"

    if email:
        print(f'{message} with e-mail "{email}":')
        if users:
            print("\t", users)
        else:
            print("\tINFO: No user found with specified e-mail!")
    else:
        print(f'{message}:')
        if not users:
            print("\tINFO: No users found in database.")
        else:
            for user_obj in users:
                print("\t", user_obj)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--email", help="Specify user e-mail", required=False)
    parser.add_argument("-a", "--authorize", help="Authorize user (1=>user, 2=>admin)", required=False, type=int,
                        default=0)
    parser.add_argument("-l", "--list", help="List devices", required=False, action='store_true')
    parser.add_argument("-d", "--delete", help="Delete specified user", required=False, action='store_true')

    args = parser.parse_args()

    connection = database.open_db()

    database.init_database(connection)

    if args.list:
        list_users(connection)
    elif args.delete:
        if args.email:
            print(f"INFO: Deleting user with email: {args.email}")
            database.delete_user(connection, email=args.email)

            print("Checking result:")
            list_users(connection, email=args.email)
        else:
            print("ERROR: Please provide email of the user to delete.")
    elif args.authorize is not None:
        if args.email:

            print(f"INFO: Authorizing user with email: {args.email}")
            database.update_user(connection, email=args.email, authorized=args.authorize)

            print("Checking result:")
            list_users(connection, email=args.email)
        else:
            print("ERROR: Please provide email of the user to authorize.")
    else:
        print("ERROR: No operation is specified.")
        parser.print_help()

    database.close_db(connection)
