import os
import datetime
import pytz

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        symbol = request.form.get("symbol")
        try:
            shares = int(request.form.get("shares"))
        except ValueError:
            return apology("Invalid shares number", 400)

        enquiry = lookup(symbol)
        if enquiry is None:
            return apology("Invalid Symbol", 400)
        if shares <= 0:
            return apology("Invalid shares number", 400)

        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
        cost = shares * enquiry["price"]
        leftover = cash - cost
        if leftover < 0:
            return apology("Not enough cash", 400)

        db.execute("UPDATE users SET cash = ? WHERE id = ?", leftover, session["user_id"])
        db.execute("INSERT INTO exchanges (user_id, time, buy, symbol, price) VALUES (?, ?, ?, ?, ?)",
                   session["user_id"], datetime.datetime.now(pytz.timezone("US/Eastern")), shares, symbol, enquiry["price"])

        return redirect("/")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT symbol, buy, sell, price, time FROM exchanges WHERE user_id = ?", session["user_id"])
    for row in history:
        row["price"] = usd(row["price"])

    return render_template("history.html", history=history)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    return redirect("/")

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote"""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        name = request.form.get("symbol")
        if not name:
            return apology("Please enter a Stock Symbol", 400)

        enquiry = lookup(name)
        if enquiry is None:
            return apology("Invalid Stock Symbol", 400)

        return render_template("quoted.html", symbol=enquiry["symbol"], price=usd(enquiry["price"]))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            return apology("Please enter all fields", 400)
        if password != confirmation:
            return apology("Passwords do not match", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        if len(rows) > 0:
            return apology("Username already exists", 400)

        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, generate_password_hash(password))

        rows = db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]

        return redirect("/")

@app.route("/")
@login_required
def index():
    grand_total = 0
    try:
        portfolio = db.execute(
            "SELECT SUM(COALESCE(buy, 0)) - SUM(COALESCE(sell, 0)) AS n, symbol FROM exchanges WHERE user_id = ? GROUP BY symbol HAVING n > 0",
            session["user_id"]
        )
    except RuntimeError:
        portfolio = []

    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"]
    grand_total += cash

    for share in portfolio:
        price = lookup(share["symbol"])["price"]
        total = price * share["n"]
        share["price"] = usd(price)
        grand_total += total
        share["total"] = usd(total)

    return render_template("index.html", portfolio=portfolio, cash=usd(cash), grand_total=usd(grand_total))

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        portfolio = db.execute(
            "SELECT symbol, SUM(COALESCE(buy, 0)) - SUM(COALESCE(sell, 0)) AS n FROM exchanges WHERE user_id = ? GROUP BY symbol HAVING n > 0",
            session["user_id"]
        )
        return render_template("sell.html", portfolio=portfolio)
    else:
        portfolio = db.execute(
            "SELECT symbol, SUM(COALESCE(buy, 0)) - SUM(COALESCE(sell, 0)) AS n FROM exchanges WHERE user_id = ? GROUP BY symbol HAVING n > 0",
            session["user_id"]
        )
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if shares <= 0:
            return apology("Invalid number of shares", 400)

        for row in portfolio:
            if row["symbol"] == symbol:
                if row["n"] >= shares:
                    price = lookup(symbol)["price"]
                    db.execute(
                        "INSERT INTO exchanges (user_id, symbol, sell, time, price) VALUES (?, ?, ?, ?, ?)",
                        session["user_id"], symbol, shares, datetime.datetime.now(pytz.timezone("US/Eastern")), price
                    )
                    db.execute(
                        "UPDATE users SET cash = cash + ? WHERE id = ?", shares * price, session["user_id"]
                    )
                    return redirect("/")
                else:
                    return apology("Selling amount exceeds holdings", 400)

        return apology("You do not own any shares of this stock", 400)

if __name__ == "__main__":
    app.run(debug=True)
