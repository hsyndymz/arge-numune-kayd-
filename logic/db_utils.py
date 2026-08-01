import sqlite3
import os
import streamlit as st

DB_DATA_PATH = 'data/numune_takip.db'
DB_SETTINGS_PATH = 'data/kesif_sistemi.db'

def get_connection():
    """Connection to the main sample database"""
    if not os.path.exists('data'):
        os.makedirs('data')
    conn = sqlite3.connect(DB_DATA_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def get_settings_connection():
    """Connection to the discovery settings and protocol history database"""
    if not os.path.exists('data'):
        os.makedirs('data')
    conn = sqlite3.connect(DB_SETTINGS_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

