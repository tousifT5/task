import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid
import yfinance as yf
from flask import redirect, render_template, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message))


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """
    Look up quote for a specific symbol using yfinance.
    Does not attempt fuzzy matching or suffix appending.
    """

    # Normalize symbol for consistent handling
    symbol_upper = symbol.upper().strip()

    try:
        print(f"DEBUG: Attempting direct lookup for symbol: {symbol_upper}") # Debugging print
        ticker = yf.Ticker(symbol_upper)

        # Get historical data for a short period (e.g., 1 day)
        # Use '1d' for the most recent day's data, or '5d' to ensure some data is returned
        hist = ticker.history(period="1d", auto_adjust=True)

        # If no data is returned, try a slightly longer period
        if hist.empty:
            hist = ticker.history(period="5d", auto_adjust=True)
        
        if not hist.empty:
            # Get the latest adjusted close price
            price = round(float(hist["Close"].iloc[-1]), 2)

            # Get the company name (longName)
            company_info = ticker.info
            name = company_info.get("longName") or company_info.get("shortName") or symbol_upper

            if price > 0: # Ensure we have a valid price
                print(f"DEBUG: Found data for {symbol_upper}: {name}, ${price}")
                return {
                    "name": name,
                    "price": price,
                    "symbol": symbol_upper
                }
            else:
                print(f"DEBUG: Price is zero or invalid for {symbol_upper}. Data might be incomplete.")
                return None
        else:
            print(f"DEBUG: No historical data found for {symbol_upper} after trying 1d and 5d periods.")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"Error (HTTP) during lookup for '{symbol_upper}': {http_err} - might be a subscription issue or invalid symbol.")
        return None
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Error (Connection) during lookup for '{symbol_upper}': {conn_err} - check internet connection or yfinance server.")
        return None
    except Exception as e:
        print(f"General error looking up '{symbol_upper}': {e}")
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
