📈 Flask Stock Quote App
Welcome to the Flask Stock Quote App! This is a simple web application that allows logged-in users to look up real-time stock prices using the yfinance Python library. It's designed to be straightforward and easy to use.

✨ What It Does
User Login: Create an account and sign in to access the features.

Stock Quote Lookup: Enter a stock symbol (like AAPL for Apple) to get its current price.

User Data: Saves your account information in a simple database file.

🚀 How It Works
This app uses a few main parts:

Flask (Backend): This is the core of the website, handling web pages, user logins, and fetching stock data.

User Accounts: It uses a tool called cs50.SQL to store usernames and secure passwords in a file named project.db.

Stock Data: The yfinance Python library is used to connect to Yahoo Finance and retrieve the latest stock prices.

🛠️ Get Started (Setup and Run)
Follow these steps to get the stock quote app running on your computer:

1. What You'll Need
Python 3.9 or newer installed on your computer.

Git (if you're downloading the project files from GitHub).

2. Get the Project Files
First, open your computer's terminal (or command prompt) and go to your project folder. If you're using Git (recommended):

git clone https://github.com/tousifT5/Stock_Market.git 

If you're not using Git, you can manually download the project files 


3. Install Necessary Tools
In your terminal, run this command to install all the required Python libraries from your requirements.txt file:

pip install -r requirements.txt

4. Set Up the User Database
After clonning or downloading you will have schema.sql, it is required to create database for application run below command in your terminal.

sqlite3 project.db < schema.sql

This command will create the project.db file (if it doesn't exist) and execute the SQL commands from schema.sql to set up your database tables.

or you can edit schema file as per your needs then run above command to create database.

5. Run the App!
Now you can start the application. In your terminal, type:

python app.py

Open your web browser and go to http://127.0.0.1:5000/.

📂 Project Files
app.py: The main code for the website, including login and stock lookup.

helpers.py: Contains helper functions like lookup (for stock data) and usd (for formatting currency).

static/project.css: Controls how the website looks.

templates/: All the website pages (apology.html, quote.html, quoted.html, register.html, login.html, layout.html).

.gitignore: Tells Git which files to ignore (like your database file).

project.db: Your user database file (created when you run the app and set up the schema).

requirements.txt: Lists all the Python libraries this app needs.

schema.sql: Contains the SQL commands to set up your database tables.
