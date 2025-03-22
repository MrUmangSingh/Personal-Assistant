import streamlit as st
import psycopg2
from psycopg2 import pool
import hashlib
import os
import pickle
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from auth import register_user, login_user, update_twitter_credentials, process_email_credentials


def chat_with_ai(message):
    # Replace with actual AI logic/API call.
    return f"AI Response to: {message}"


def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.page = "login"


def login_page():
    st.title("Welcome to Orion 🌟")
    st.markdown("### Your Personalized Personal Assistant")
    with st.form("login_form"):
        username = st.text_input("Username", key="username_input")
        password = st.text_input(
            "Password", type="password", key="password_input")
        submitted = st.form_submit_button("Login")
    if submitted:
        if login_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome {username}!")
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("Incorrect username or password")
    if st.button("Don't have an account? Register here."):
        st.session_state.page = "register"
        st.rerun()


def register_page():
    st.title("Register for Orion")
    st.markdown("### Create Your Account")
    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    new_pass_confirm = st.text_input("Confirm Password", type="password")
    if st.button("Sign Up"):
        if new_pass != new_pass_confirm:
            st.error("Passwords do not match")
        elif len(new_pass) < 8:
            st.error("Password must be at least 8 characters")
        elif register_user(new_user, new_pass):
            st.success("Registration successful! Please login.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error("Username already exists")
    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()


def dashboard():
    # Sidebar: Configuration for Twitter and Email
    st.sidebar.title("Configuration")

    # Twitter API Credentials
    twitter_consumer_key = st.sidebar.text_input(
        "Twitter Consumer Key", key="twitter_consumer_key_input")
    twitter_consumer_secret = st.sidebar.text_input(
        "Twitter Consumer Secret", key="twitter_consumer_secret_input")
    twitter_access_token = st.sidebar.text_input(
        "Twitter Access Token", key="twitter_access_token_input")
    twitter_access_secret = st.sidebar.text_input(
        "Twitter Access Secret", key="twitter_access_secret_input")
    if st.sidebar.button("Save Twitter Credentials"):
        update_twitter_credentials(
            st.session_state.username, twitter_consumer_key, twitter_consumer_secret, twitter_access_token, twitter_access_secret)

    # Email Credentials: File uploader for credentials.json
    uploaded_credentials = st.sidebar.file_uploader(
        "Upload credentials.json for Email Access", type=["json"])
    if uploaded_credentials is not None:
        if st.sidebar.button("Generate Email Token"):
            process_email_credentials(uploaded_credentials)

    st.sidebar.button("Logout", on_click=logout)

    # Main content: Chat interface
    st.title(f"Welcome {st.session_state.username}!")
    st.header("Chat with Orion AI")

    # Initialize chat history in session state if not already present
    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    # Chat input using st.chat_input
    question = st.chat_input("Chat with Orion")
    if question:
        st.session_state["chat"].append({
            "role": "user",
            "content": question
        })
        response = chat_with_ai(question)  # Replace with actual AI integration
        st.session_state["chat"].append({
            "role": "assistant",
            "content": response
        })

    # Display chat history
    for chat in st.session_state["chat"]:
        st.chat_message(chat['role']).markdown(chat['content'])


if __name__ == '__main__':
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if st.session_state.logged_in and st.session_state.page == "dashboard":
        dashboard()
    else:
        if st.session_state.page == "login":
            login_page()
        elif st.session_state.page == "register":
            register_page()
        else:
            login_page()
