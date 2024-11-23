# Wizard101-Quiz-Solver
A python project utilizing selenium to solve the daily quizzes for free crowns.

In order for this program to work, please create a .env file with the following variables:

WIZ_USERNAME = {enter your username}
WIZ_PASSWORD = {enter your password}

This program utilizes OpenAI's whisper recognition model.
Please follow the guide to installing Whisper. https://github.com/openai/whisper
For more information about the whisper package, check out https://openai.com/index/whisper/

Additionally, please install the following requirements using 'pip install':
- selenium
- requests


Then run the script and it should auto-solve trivia questions.
Current limitations include reCAPTCHA's ability to recognize auto-solving. For these reCAPTCHAs, you must solve them manually. 
Once solved, the program will continue execution.
