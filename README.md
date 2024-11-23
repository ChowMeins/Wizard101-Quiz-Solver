# Wizard101-Quiz-Solver
A python project utilizing selenium to solve the daily quizzes for free crowns.

In order for this program to work, please create a .env file with the following variables:

WIZ_USERNAME = {enter your username}
WIZ_PASSWORD = {enter your password}

Then run pip install -r requirements.txt
(optionally, you can create a virtual environment if needed)

Then run the script and it should auto-solve trivia questions.
A limitation for this project would be dealing with reCAPTCHAs that prevent the script
from continuing. For these reCAPTCHAs, you must solve them manually. Once solved, the program will continue execution.
