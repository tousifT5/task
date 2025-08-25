import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

from datetime import datetime, timezone # time_now() function is removed as per fixes

from stock_dash import init_dash_app
# Configure application
app = Flask(__name__)
dash_app_instance = init_dash_app(app)
# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Create new table, and index (for efficient search later on) to keep track of stock orders, by each user
db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, cash NUMERIC NOT NULL DEFAULT 10000.00);")

# NOTE: The 'portfolio' table is created but not used in the current Python logic.
# Consider implementing logic to update it or removing this table creation if not needed.
db.execute("CREATE TABLE IF NOT EXISTS portfolio ( id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL, \
        symbol TEXT NOT NULL,shares INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id));"
        )

# Corrected 'history' table schema. 'transacted_at' will auto-fill with CURRENT_TIMESTAMP.
db.execute("CREATE TABLE IF NOT EXISTS history ( id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, \
        symbol TEXT NOT NULL, shares INTEGER NOT NULL, method TEXT NOT NULL, price NUMERIC NOT NULL, \
        transacted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id));"
        )

# Make sure API key is set

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    owns = own_shares()
    total = 0
    for symbol, shares in owns.items():
        result = lookup(symbol)
        if result: # Check if lookup was successful
            name, price = result["name"], result["price"]
            stock_value = shares * price
            total += stock_value
            owns[symbol] = (name, shares, usd(price), usd(stock_value))
        else:
            # Handle case where lookup fails for a symbol in user's portfolio
            # This could happen if a ticker symbol becomes invalid.
            # You might want to display a message or remove the invalid symbol.
            owns[symbol] = (f"{symbol} (Lookup Failed)", shares, usd(0), usd(0))
            flash(f"Warning: Could not get current data for {symbol}.", "warning")

    cash = db.execute("SELECT cash FROM users WHERE id = ? ", session["user_id"])[0]['cash']
    total += cash
    return render_template("index.html", owns=owns, cash= usd(cash), total = usd(total))


@app.route("/buy", methods=["GET", "POST"])
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    # POST request logic
    symbol = request.form.get("symbol")
    shares_str = request.form.get("shares")

    if not symbol:
        return apology("must provide symbol")
    if not shares_str or not shares_str.isdigit() or int(shares_str) <= 0:
        return apology("must provide a positive number of shares")

    shares_to_buy = int(shares_str)
    result = lookup(symbol)


    if not result:
        # Improved error message for invalid symbol
        not_found_msg = f"Could not find stock for '{symbol}'. Try adding an exchange suffix, e.g., 'TATAMOTORS.NS' for Indian stocks, 'D05.SI' for Singapore stocks, or 'OR.PA' for L'Oréal."
        return apology(not_found_msg)

    name = result["name"]
    price = result["price"]
    # Ensure the symbol from lookup is used for consistency, as it might be standardized
    standardized_symbol = result["symbol"]

    user_id = session["user_id"]
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]['cash']

    # Check if user can afford the purchase
    total_cost = price * shares_to_buy
    remain_cash = cash - total_cost

    if remain_cash < 0:
        return apology("Insufficient Cash. Failed Purchase.")

    # Deduct order cost from user's remaining balance (i.e. cash)
    db.execute("UPDATE users SET cash = ? WHERE id = ?", remain_cash, user_id)

    # Log the transaction into history
    method = "BUY"
    db.execute("INSERT INTO history (user_id, symbol, shares, price, method) VALUES (?, ?, ?, ?, ?)", \
                                     user_id, standardized_symbol, shares_to_buy, price, method)

    # --- Start of CORRECTED portfolio update logic ---
    # Check if user already owns this stock in their portfolio table
    current_portfolio_shares = db.execute(
        "SELECT shares FROM portfolio WHERE user_id = ? AND symbol = ?",
        user_id, standardized_symbol
    )

    if current_portfolio_shares:
        # If stock exists in portfolio, update the shares
        existing_shares = current_portfolio_shares[0]['shares']
        new_total_shares = existing_shares + shares_to_buy
        db.execute(
            "UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?",
            new_total_shares, user_id, standardized_symbol
        )
    else:
        # If stock does not exist, insert a new entry
        db.execute(
            "INSERT INTO portfolio (user_id, symbol, shares) VALUES (?, ?, ?)",
            user_id, standardized_symbol, shares_to_buy
        )
    # --- End of CORRECTED portfolio update logic ---

    flash(f"Bought {shares_to_buy} shares of {name} ({standardized_symbol}) for {usd(total_cost)}!")
    return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # FIX: Corrected SELECT statement to use 'transacted_at'
    rows = db.execute("SELECT symbol, shares, price, method, transacted_at FROM history WHERE user_id = ? ORDER BY transacted_at DESC", session["user_id"])

    # Format prices and shares for display
    formatted_rows = []
    for row in rows:
        # Shares are negative for sells, positive for buys
        formatted_shares = row['shares']
        # Price is per share
        formatted_price = usd(row['price'])
        # Calculate total value for each transaction
        total_value = usd(abs(row['shares']) * row['price'])
        formatted_rows.append({
            'symbol': row['symbol'],
            'shares': formatted_shares,
            'price': formatted_price,
            'total_value': total_value,
            'method': row['method'],
            'transacted_at': row['transacted_at']
        })
    return render_template("history.html", rows=formatted_rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        print(rows)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")

    # POST request logic
    symbol = request.form.get("symbol")
    if not symbol:
        return apology("must provide symbol")

    result = lookup(symbol)
    not_found_msg = f"Could not find stock for '{symbol}'. Try adding an exchange suffix, e.g., 'TATAMOTORS.NS' for Indian stocks, 'D05.SI' for Singapore stocks, or 'OR.PA' for L'Oréal."
    suggestion_message = "For better results, try adding an exchange suffix, e.g., 'TATAMOTORS.NS' for Indian stocks, 'D05.SI' for Singapore stocks."

    if not result:
        return render_template("quote.html", invalid=True, symbol=symbol, message=not_found_msg)

    return render_template("quoted.html", name=result["name"], price=usd(result["price"]), symbol=result["symbol"], message=suggestion_message)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    # check username and password
    username = request.form.get("username")
    password = request.form.get("password")
    confirmation = request.form.get("confirmation")

    if not username:
        return apology("must provide username")
    if len(db.execute('SELECT username FROM users WHERE username = ?', username)) > 0:
        return apology("username already exists")
    if not password:
        return apology("must provide password")
    if password != confirmation:
        return apology("passwords do not match")

    # Add new user to users db (includes: username and HASH of password)
    db.execute('INSERT INTO users (username, hash) VALUES(?, ?)', username, generate_password_hash(password))

    # Query database for username
    rows = db.execute("SELECT * FROM users WHERE username = ?", username)
    # Log user in, i.e. Remember that this user has logged in
    session["user_id"] = rows[0]["id"]
    print(session["user_id"])
    # Redirect user to home page
    flash("Registered and logged in!")
    return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock; Similar to /buy, with negative # shares"""
    owns = own_shares()
    if request.method == "GET":
        # Ensure only stocks the user owns are listed for selling
        return render_template("sell.html", owns=owns.keys())

    symbol = request.form.get("symbol")
    shares_str = request.form.get("shares")

    if not symbol:
        return apology("must provide symbol")
    if not shares_str or not shares_str.isdigit() or int(shares_str) <= 0:
        return apology("must provide a positive number of shares")

    shares_to_sell = int(shares_str)

    # Check whether there are sufficient shares to sell
    if symbol not in owns or owns[symbol] < shares_to_sell:
        flash(f"You only own {owns.get(symbol, 0)} shares of {symbol}.", "warning")
        return apology("Insufficient shares owned to sell")

    # Execute sell transaction: look up sell price, and add fund to cash,
    result = lookup(symbol)
    if not result:
        return apology(f"Could not get current price for {symbol}.")
    owns_shares = owns[symbol] 
    new_share = int(owns_shares) - int(shares_to_sell)
    print(owns[symbol])
    print(owns_shares)
    print(shares_to_sell)
    print(new_share)
    print("DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDd")
    user_id = session["user_id"]
    current_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]['cash']
    sell_price_per_share = result["price"]
    total_sale_value = sell_price_per_share * shares_to_sell
    new_cash_balance = current_cash + total_sale_value

    db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash_balance, user_id)

    # Log the transaction into history with negative shares for a sell
    method = "SELL"
    # FIX: Corrected INSERT statement to match history table schema and use default timestamp
    db.execute("INSERT INTO history (user_id, symbol, shares, price, method) VALUES (?, ?, ?, ?, ?)", \
                                     user_id, symbol, shares_to_sell, sell_price_per_share, method)

    db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?", \
                                     new_share,user_id, symbol)

    flash(f"Sold {shares_to_sell} shares of {result['name']} ({symbol}) for {usd(total_sale_value)}!")
    return redirect("/")


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    return redirect("/dashboard/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


def own_shares():
    """Helper function: Which stocks the user owns, and numbers of shares owned. Return: dictionary {symbol: qty}"""
    user_id = session["user_id"]
    owns = {}
    query = db.execute("SELECT symbol, shares FROM portfolio WHERE user_id = ?", user_id)
    for q in query:
        symbol, shares = q["symbol"], q["shares"]
        owns[symbol] = owns.setdefault(symbol, 0) + shares
    # Filter zero-share stocks
    owns = {k: v for k, v in owns.items() if v != 0}
    return owns

# The time_now() function is no longer needed if transacted_at uses DEFAULT CURRENT_TIMESTAMP
# def time_now():
#     """HELPER: get current UTC date and time"""
#     now_utc = datetime.now(timezone.utc)
#     return str(now_utc.date()) + ' @time ' + now_utc.time().strftime("%H:%M:%S")


if __name__ == "__main__":
    app.run(debug=True)