# CS50x-Finance
Developed a dynamic web application using Flask, Python, SQL, and JavaScript, as part of the CS50x curriculum. This application simulates a personal finance manager.


# O Finance

O Finance is a dynamic web application developed as part of the **CS50x curriculum**, simulating a personal finance manager with robust features for stock management and user portfolio tracking.

## Features

- **User Authentication**  
  - Secure user registration and login system to protect user data.

- **Stock Management**  
  - Allows users to quote, buy, and sell stocks in real-time.

- **Portfolio Overview**  
  - Displays a comprehensive view of the user's stock portfolio, including current prices, stock holdings, and total value.

- **Transaction History**  
  - Maintains a detailed record of all user transactions for future reference.

## Technologies Used

- **Backend**: Flask, Python, SQL
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/o-finance.git
# Navigate to the project directory:
cd o-finance
# Install Dependencies
pip install -r requirements.txt
#Set-up The Data-base
flask db upgrade
#Run the application:
flask run
