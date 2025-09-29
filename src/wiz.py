import random
import time
import playwright
from playwright.sync_api import sync_playwright, Page, Browser, Frame
import datetime
import json
from collections import defaultdict
import os
from dotenv import load_dotenv
from exceptions import *
from transcribe import transcribe_audio

class QuizBot:
    def __init__(self):
        load_dotenv()
        self.username: str = os.getenv("WIZ_USERNAME")
        self.password: str = os.getenv("WIZ_PASSWORD")
        if not self.username or not self.password:
            raise LoginException("Username or password not found in environment variables")
        
        try:
            with open("quizzes.json", "r") as f:
                self.quizzes = json.load(f)
        except FileNotFoundError as e:
            raise FileLoadingException(f"quizzes.json file not found: {e}")
        except json.decoder.JSONDecodeError as e:
            raise FileLoadingException(f"Invalid JSON in quizzes.json: {e}")
        
        try:
            with open("nontrivia_urls.txt", "r") as f:
                self.nontrivia_urls = set(line.strip() for line in f.readlines() if line.strip())
        except FileNotFoundError:
            raise FileLoadingException("Warning: nontrivia_urls.txt file not found. Quiz titles may not be directed to the correct URL...")

        # Insert any trivia title to testing these quizzes first
        self.all_quiz_titles: list = list(self.quizzes.keys())
        random.shuffle(self.all_quiz_titles)
        # Shuffle once and take the first 10
        self.quiz_samples: list = self.all_quiz_titles[:10]
        self.all_quiz_titles = self.all_quiz_titles[10:]

        self.browser: Browser = None
        self.page: Page = None

    def setup_browser(self, p):
        """Initialize browser and login"""
        try:
            self.browser = p.firefox.launch(headless=False)
            context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
            )
            self.page = context.new_page()
            self.page.goto("https://www.wizard101.com/game", wait_until="networkidle")
            
            # Login
            print(f"Attempting login with username: {self.username}")
            self.page.locator("input[id='loginUserName']").fill(self.username)
            self.page.locator("input[id='loginPassword']").fill(self.password)
            
            with self.page.expect_navigation(wait_until="networkidle"):
                self.page.locator("div[class='wizardButtonInput']").click()
            print("Login successful!")
        except Exception as e:
            raise LoginException(f"Failed to setup browser or login: {e}")

    def navigate_to_quiz(self, title: str):
        """ Edit the title string and navigate to the quiz URL """
        try:
            trivia_title = "-".join(title.strip().lower().split(" "))
            quiz_url = "https://www.wizard101.com/quiz/trivia/game/" + trivia_title
            if title not in self.nontrivia_urls:
                quiz_url += "-trivia"
            self.page.goto(quiz_url, wait_until="networkidle")
        except Exception as e:
            raise NavigationException(f"Failed to navigate to quiz: {e}")
        
    def is_quiz_completed(self, title: str):
        """ Check if quiz has already been completed today """
        try:
            quiz_completed = self.page.locator("div[class='quizThrottle']")
            quiz_completed.wait_for(state="visible", timeout=3000)
            raise QuizCompletedException(f"Quiz '{title}' has already been completed for today. Skipping...")
        except QuizCompletedException:
            raise
        except:
            return False
        
    def solve_quiz(self, title: str):
        # Initialize answer key as defaultdict of lists
        answer_key = defaultdict(list)
        for question in self.quizzes[title]:
            answer_key[question[0]].append(question[1])

        quiz_finished = False
        quiz_question_count = 1
        # Answer the 12 questions in the quiz
        while quiz_finished == False:
            # If the questions exceed a count of 20, end program
            if quiz_question_count >= 20:
                raise QuizProcessingException(f"Quiz Question exceeded limit. An error has occured.")
            
            # Parse question text
            try:
                question_text = self.page.locator("div[class='quizQuestion']")
                question_text.wait_for(state="visible", timeout=5000)
                question_text = question_text.inner_text().strip()
            except Exception as e:
                # If the question text is not found, check if the quiz is completed by searching for the 'Claim Your Reward' Button
                try:
                    claim_rewards_button = self.page.locator("a[class*='kiaccountsbuttongreen']", has_text="CLAIM YOUR REWARD")
                    claim_rewards_button.wait_for(state="visible")
                    quiz_finished = True
                    quiz_question_count = 1 # Reset question count for next quiz
                    break
                except Exception as e:
                    raise QuizProcessingException(f"Quiz question not found, but Claim Rewards button not found either: {e}")
                
            # Parse each answer choice
            try:
                answer_container = self.page.locator("div[class='answersContainer']")
                answer_choice = answer_container.locator("div[class*='answer']").all() # 0 - Quiz Answer Box, 1 - Quiz Text
                answer_choice = [[answer.locator("a[name='checkboxtag']"), answer.locator("span[class='answerText']")] for answer in answer_choice]
                correct_answer_found = False
            except Exception as e:
                raise QuizProcessingException(f"Error parsing answer choices: {e}")
            
            # Select the correct answer if it exists in the answer key
            try:
                for answer in answer_choice:
                    answer[1].wait_for(state="visible") # Wait for answer text to appear
                    answer_text = answer[1].inner_text().strip()
                    if answer_text in answer_key[question_text]:
                        answer[0].wait_for(state="visible") # Wait for checkbox to appear
                        self.page.wait_for_timeout(random.uniform(1000,1500))
                        answer[0].click()
                        correct_answer_found = True
                        continue
                # Otherwise, select the first answer choice and log the question
                if not correct_answer_found:
                    os.makedirs("../logs", exist_ok=True)
                    with open("../logs/new_questions.txt", "a", encoding="utf-8") as f:
                        f.write(f"Quiz Title: {title}\nQuestion: {question_text}\nAnswer choices:\n")
                        for answer in answer_choice:
                            answer_text = answer[1].inner_text().strip()
                            f.write(f"- {answer_text}\n")
                        f.write("\n")
                    answer_choice[0][0].wait_for(state="visible")
                    self.page.wait_for_timeout(random.uniform(1000,1500))
                    answer_choice[0][0].click()
            except Exception as e:
                raise QuizProcessingException(f"Error selecting correct answer: {e}")

            # Click the Next Question button
            try:
                next_question_button = self.page.locator("button[id='nextQuestion']")
                # Wait for both the fadeIn class AND visibility
                self.page.wait_for_function(
                    """() => {
                        const button = document.getElementById('nextQuestion');
                        return button && 
                            button.classList.contains('fadeIn') && 
                            (button.style.visibility === 'visible' || getComputedStyle(button).visibility === 'visible');
                    }"""
                )
                self.page.wait_for_timeout(random.uniform(1000,1500))
                next_question_button.click()
            except Exception as e:
                raise QuizProcessingException(f"Error clicking Next Question button: {e}")
            
            quiz_question_count += 1

        return True

    def claim_rewards(self):
        # Claim rewards after completing all questions
        try:
            self.page.wait_for_load_state("networkidle")
            claim_rewards_button = self.page.locator("a[class*='kiaccountsbuttongreen']", has_text="CLAIM YOUR REWARD")
            claim_rewards_button.wait_for(state="visible")
            claim_rewards_button.click()
        except Exception as e:
            timestamp = datetime.datetime.now().strftime("%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            os.makedirs("../snapshots", exist_ok=True)
            self.page.screenshot(path=f'../snapshots/{filename}')
            raise QuizProcessingException(f"Error claiming rewards: {e}")
        

        # Handle reward iframe and log results
        try:
            self.page.wait_for_load_state("networkidle")
            self.page.wait_for_selector("iframe[id='jPopFrame_content']", state="visible")
            reward_iframe = self.page.frame_locator("iframe[id='jPopFrame_content']")
            reward_submit = reward_iframe.locator("a[id='submit'], a[class='buttonsubmit']")
            reward_submit.wait_for(state="visible")
            self.page.wait_for_timeout(random.uniform(1000,1500))
            reward_submit.click()
        except Exception as e:
            raise QuizProcessingException(f"Error handling reward iframe: {e}")
        
        # Check for reCAPTCHA popup
        try:
            recaptcha_iframe = reward_iframe.locator("iframe[title*='recaptcha']")
            recaptcha_iframe.wait_for(state="visible", timeout=5000)
            recaptcha_iframe = reward_iframe.frame_locator("iframe[title*='recaptcha']")
            self.solve_recaptcha(reward_iframe = reward_iframe, recaptcha_iframe = recaptcha_iframe)
        except RecaptchaFailedException:
            raise RecaptchaFailedException(f"Error solving reCAPTCHA: {e}")
        except Exception as e:
            # No reCAPTCHA found, quiz may be solved without needing to do reCAPTCHA
            pass
        return True


    def solve_recaptcha(self, reward_iframe: Frame, recaptcha_iframe: Frame):   
        # If reCAPTCHA is found, switch to audio challenge
        try:
            audio_button = recaptcha_iframe.locator("button[id='recaptcha-audio-button']")
            audio_button.wait_for(state="visible")
            self.page.wait_for_timeout(random.uniform(2000,2500))
            audio_button.click()
            #print("reCAPTCHA challenge detected. Solving now...")
        except Exception as e:
            raise RecaptchaFailedException(f"Error trigger audio reCAPTCHA challenge: {e}")

        recaptcha_solved = False
        while recaptcha_solved == False:
            # Press 'PLAY' button
            try:
                audio_div = recaptcha_iframe.locator("div[class='rc-audiochallenge-control']")
                play_audio_button = audio_div.locator("button", has_text="PLAY")
                play_audio_button.wait_for(state="visible", timeout=5000)
                self.page.wait_for_timeout(random.uniform(2000,2500))
                play_audio_button.click()
            except Exception as e:
                # Indicates that reCAPTCHA detected automated queries, simply skips the quiz and adds a new quiz to the quiz_samples 
                raise RecaptchaFailedException(f"Error pressing PLAY button: {e}")
            
            # Get audio URL
            try:
                audio_source = audio_div.locator("audio[id='audio-source']")
                audio_url = audio_source.get_attribute("src")
            except Exception as e:
                raise RecaptchaFailedException(f"Error retrieving audio URL: {e}")
            
            # Transcribe audio using faster-whisper and enter it into the input area
            try:
                captcha_solution_text = transcribe_audio(audio_url)
                captcha_input = recaptcha_iframe.locator("input[id='audio-response']")
                #print(f"Transcribed audio: {captcha_solution_text}")
                captcha_input.type(text=captcha_solution_text, delay=100)
            except Exception as e:
                raise RecaptchaFailedException(f"Error inputting transcribed audio: {e}")

            # Click the Verify button
            try:
                verify_button = recaptcha_iframe.locator("button[id='recaptcha-verify-button']")
                verify_button.wait_for(state="visible")
                self.page.wait_for_timeout(random.uniform(1000,1500))
                verify_button.click()
                #print("Submitted reCAPTCHA solution. Waiting for verification...")
            except Exception as e:
               raise RecaptchaFailedException(f"Error clicking Verify button: {e}")

            # Check if the reCAPTCHA iframe is still present, solve again if so (usually means solution was incorrect or multiple solutions are required)
            try:
                recaptcha_presence = reward_iframe.frame_locator("iframe[title*='recaptcha']")
                recaptcha_presence.wait_for(state="visible", timeout=5000)
                reload_button = recaptcha_iframe.locator("button[id='recaptcha-reload-button']")
                reload_button.wait_for(state="visible")
                reload_button.click()
                #print("Multiple reCAPTCHA solutions required. Retrying...")
            # Break from the loop if the reCAPTCHA was solved successfully
            except:
                recaptcha_solved = True
                #print("reCAPTCHA solved successfully.")
                break
        return True
                
    def log_quiz_results(self, title: str):
        # Log quiz results if 100% score not achieved
        try:
            self.page.wait_for_load_state("networkidle")
            quiz_score = self.page.locator("div[class*='quizScore']")
            quiz_score.wait_for(state="visible")
            quiz_score = quiz_score.inner_text().strip()
            if quiz_score != "100%":
                os.makedirs("../logs", exist_ok=True)
                with open("../logs/quiz_log.txt", "a", encoding="utf-8") as log_file:
                    log_file.write(f"Quiz '{title}' completed with score: {quiz_score}\n\n")
                    show_answers = self.page.locator("a", has_text="See correct answers!")
                    show_answers.wait_for(state="visible")
                    show_answers.click()
                    quiz_results = self.page.locator("div[id='quizResults']")
                    quiz_results.wait_for(state="visible")
                    log_file.write(f"{quiz_results.inner_text()}\n\n")
            print(f"Quiz '{title}' completed with score: {quiz_score}")
        except Exception as e:
            raise QuizProcessingException(f"Error logging quiz results: {e}")

    def take_screenshot(self):
        """Take screenshot for debugging"""
        try:
            timestamp = datetime.datetime.now().strftime("%m-%d_%H-%M-%S")
            filename = f"screenshot_{timestamp}.png"
            os.makedirs("../snapshots", exist_ok=True)
            if self.page:
                self.page.screenshot(path=f'../snapshots/{filename}')
                print(f"Screenshot saved: {filename}")
        except Exception as e:
            print(f"Error taking screenshot: {e}")

    def run(self):
        with sync_playwright() as p:
            try:
                self.setup_browser(p)

                while self.quiz_samples:
                    title = self.quiz_samples.pop(0)

                    try: 
                        self.navigate_to_quiz(title)
                        self.is_quiz_completed(title)
                        self.solve_quiz(title)
                        self.claim_rewards()
                        self.log_quiz_results(title)
                        
                    except QuizCompletedException:
                        print(f"Quiz '{title}' has already been completed today. Skipping...")
                        continue
                    
                    # If reCAPTCHA fails to get solved, simply add a new quiz, and start the browser up again.
                    except RecaptchaFailedException as e:
                        print(f"reCAPTCHA failed for quiz '{title}': {e}")
                        if self.all_quiz_titles:
                            self.quiz_samples.append(self.all_quiz_titles.pop(0))
                        
                        self.browser.close()
                        self.setup_browser(p)
                        
                    except (NavigationException, QuizProcessingException) as e:
                        print(f"Error processing quiz '{title}': {e}")
                        self.take_screenshot()
            except LoginException as e:
                print(f"Login failed: {e}")
                return
            finally:
                if self.browser:
                    self.browser.close()
def main():
    try:
        quizBot = QuizBot()
        quizBot.run()
    except Exception as e:
        print(f"Fatal error occured: {e}")

if __name__ == "__main__":
    main()