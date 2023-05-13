#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create users in bulk

@author: Hrishikesh Terdalkar
"""

###############################################################################

from typing import List
from flask import Flask
from flask_security import Security, hash_password

# Local
from settings import app
from models_sqla import db, user_datastore
from models_sqla import CustomLoginForm

###############################################################################

webapp = Flask(__name__)
webapp.config['SECRET_KEY'] = app.secret_key
webapp.config['SECURITY_PASSWORD_SALT'] = app.security_password_salt
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
webapp.config['SQLALCHEMY_DATABASE_URI'] = app.sqla['database_uri']
webapp.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
}

db.init_app(webapp)
security = Security(webapp, user_datastore, login_form=CustomLoginForm)
webapp.app_context().push()

###############################################################################


def create_user(
    username: str,
    email: str,
    password: str,
    roles: List[str],
    commit=True
):
    """Create a single user"""
    if not user_datastore.find_user(username=username):
        user = user_datastore.create_user(
            username=username,
            email=email,
            password=hash_password(password),
            roles=roles
        )
        if commit:
            db.session.commit()
        return user


def bulk_create_users(users_file: str):
    """Create users in bulk

    Parameters
    ----------
    users_file : str
        Path to CSV file containing user account details
    """
    with open(users_file, encoding="utf-8") as f:
        users_data = [
            line.split(",")
            for line in f.read().split("\n")
            if line.strip()
        ]

    users = []
    for user_data in users_data:
        username = user_data[0].strip()
        email = user_data[1].strip()
        password = user_data[2].strip()
        roles = user_data[3].strip().split(" ")
        user = create_user(
            username=username,
            email=email,
            password=password,
            roles=roles,
            commit=False
        )
        if user is not None:
            users.append(user)

    if users:
        db.session.commit()
        return users


###############################################################################

if __name__ == "__main__":
    import os
    import argparse
    parser = argparse.ArgumentParser(description="Bulk create users")
    parser.add_argument(
        "input",
        help="CSV file containing user account details"
    )
    args = vars(parser.parse_args())

    if os.path.isfile(args["input"]):
        bulk_create_users(args["input"])
    else:
        print("Please provide input file.")
