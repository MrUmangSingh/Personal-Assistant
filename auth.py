import streamlit as st
import psycopg2
from psycopg2 import pool
import hashlib
import os
import pickle
import json
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()


@st.cache_resource
def init_db_pool():
    return psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )


def init_db():
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    twitter_consumer_key TEXT,
                    twitter_consumer_secret TEXT,
                    twitter_access_token TEXT,
                    twitter_access_secret TEXT
                )
            """)
            conn.commit()
    except psycopg2.Error as e:
        st.error(f"Database initialization error: {e}")
    finally:
        db_pool.putconn(conn)


global db_pool
db_pool = init_db_pool()
init_db()


def hash_password(password):
    salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256', password.encode(), salt.encode(), 100000
    )
    return salt + pwd_hash.hex()


def verify_password(stored_password, provided_password):
    salt = stored_password[:32]
    stored_hash = stored_password[32:]
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256', provided_password.encode(), salt.encode(), 100000
    )
    return pwd_hash.hex() == stored_hash


def register_user(username, password):
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hash_password(password))
            )
            conn.commit()
            return True
    except psycopg2.IntegrityError:
        return False  # Username already exists
    except psycopg2.Error as e:
        st.error(f"Registration error: {e}")
        return False
    finally:
        db_pool.putconn(conn)


def login_user(username, password):
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
            if result and verify_password(result[0], password):
                return True
            return False
    except psycopg2.Error as e:
        st.error(f"Login error: {e}")
        return False
    finally:
        db_pool.putconn(conn)


def update_twitter_credentials(username, consumer_key, consumer_secret, access_token, access_secret):
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET twitter_consumer_key = %s, twitter_consumer_secret = %s, twitter_access_token = %s, twitter_access_secret = %s WHERE username = %s",
                (consumer_key, consumer_secret,
                 access_token, access_secret, username)
            )
            conn.commit()
            st.success("Twitter credentials updated successfully!")
    except psycopg2.Error as e:
        st.error(f"Error updating Twitter credentials: {e}")
    finally:
        db_pool.putconn(conn)


def process_email_credentials(uploaded_file):
    # Save the uploaded file temporarily as credentials.json
    with open("credentials.json", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Define the Gmail scope (modify if you need additional scopes)
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    try:
        # Run the OAuth flow to obtain credentials
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

        st.success("Email token generated and stored successfully!")
    except Exception as e:
        st.error(f"An error occurred during email authentication: {e}")
