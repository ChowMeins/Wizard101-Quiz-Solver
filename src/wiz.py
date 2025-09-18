import random
import time
from playwright.sync_api import sync_playwright
import datetime
import json
from collections import defaultdict
import os
from dotenv import load_dotenv
from transcribe import transcribe_audio

def main():
    load_dotenv()
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False, args=['--mute-audio'])
        # Navigate to Wizard101 login page
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto("https://www.wizard101.com/game", wait_until=("networkidle"))
        except Exception as e:
            print(f"Error navigating to the page: {e}")
            browser.close()
            return
        

        '''

        Log in user to their Wizard 101 account.

        '''
        # Enter user info to login
        try:
            print("Attempting login with username:", os.getenv("WIZ_USERNAME"))
            login_input, password_input = page.locator("input[id='loginUserName']"), page.locator("input[id='loginPassword']")
            login_input.wait_for(state="visible")
            password_input.wait_for(state="visible")
            login_input.fill(os.getenv("WIZ_USERNAME"))
            password_input.fill(os.getenv("WIZ_PASSWORD"))
            login_button = page.locator("div[class='wizardButtonInput']")
            with page.expect_navigation(wait_until="networkidle") as popup_info:
                login_button.click()
            print("Login successful!")
        except Exception as e:
            print(f"Error during login: {e}")
            browser.close()
            return

        with open("quizzes.json", "r") as f:
            quizzes = json.load(f)

        with open("nontrivia_urls.txt", "r") as f:
            nontrivia_urls = set(line.strip() for line in f.readlines() if line.strip())


        '''

        Load quiz data, quiz titles, and the sample of 10 that will be solved

        '''
        # Insert any trivia title to testing these quizzes first
        all_quiz_titles = list(quizzes.keys())
        random.shuffle(all_quiz_titles)
        # Shuffle once and take the first 10
        quiz_samples: list = all_quiz_titles[:10]
        all_quiz_titles = all_quiz_titles[10:]
        print(quiz_samples)
        

        '''
        
        Loop through each quiz in the quiz samples

        '''
        while quiz_samples:  
            # Load each quiz
            title = quiz_samples.pop(0)
            try:
                trivia_title = "-".join(title.strip().lower().split(" "))
                quiz_url = "https://www.wizard101.com/quiz/trivia/game/" + trivia_title
                if title not in nontrivia_urls:
                    quiz_url += "-trivia"
                page.goto(quiz_url, wait_until="networkidle")
            except Exception as e:
                print("Failed to navigate to quiz URL:", e)
                browser.close()
                return
            
            try:
                quiz_completed = page.locator("div[class='quizThrottle']")
                quiz_completed.wait_for(state="visible", timeout=3000)
                print(f"Quiz '{title}' has already been completed for today. Skipping...")
                continue
            except:
                #print(f"Starting quiz: {title}")
                pass

            # Initialize answer key as a dictionary of lists (each list contains answers for a question)
            try:
                answer_key = defaultdict(list)
                for question in quizzes[title]:
                    answer_key[question[0]].append(question[1])
            except Exception as e:
                print(f"Error constructing answer key for quiz '{title}': {e}")
                browser.close()
                return
            

            '''
            
            Solve the quiz and answer all questions

            '''
            quiz_finished = False
            quiz_question_count = 1
            # Answer the 12 questions in the quiz
            while quiz_finished == False:
                # If the questions exceed a count of 20, end program
                if quiz_question_count >= 20:
                    print(f"Quiz Question exceeded limit. An error has occured.")
                    browser.close()
                    return()
                
                # Parse question text
                try:
                    question_text = page.locator("div[class='quizQuestion']")
                    question_text.wait_for(state="visible", timeout=5000)
                    question_text = question_text.inner_text().strip()
                    #print(f"Question #{quiz_question_count}: {question_text}")
                except Exception as e:
                    # If the question text is not found, check if the quiz is completed by searching for the 'Claim Your Reward' Button
                    try:
                        claim_rewards_button = page.locator("a[class*='kiaccountsbuttongreen']", has_text="CLAIM YOUR REWARD")
                        claim_rewards_button.wait_for(state="visible")
                        quiz_finished = True
                        quiz_question_count = 1 # Reset question count for next quiz
                        continue
                    except Exception as e:
                        print(f"Quiz question not found, but Claim Rewards button not found either: {e}")
                        browser.close()
                        return
                    
                # Parse each answer choice
                try:
                    answer_container = page.locator("div[class='answersContainer']")
                    answer_choice = answer_container.locator("div[class*='answer']").all() # 0 - Quiz Answer Box, 1 - Quiz Text
                    answer_choice = [[answer.locator("a[name='checkboxtag']"), answer.locator("span[class='answerText']")] for answer in answer_choice]
                    correct_answer_found = False
                except Exception as e:
                    print(f"Error parsing answer choices: {e}")
                    browser.close()
                    return
                
                # Select the correct answer if it exists in the answer key
                try:
                    for answer in answer_choice:
                        answer[1].wait_for(state="visible")
                        answer_text = answer[1].inner_text().strip()
                        if answer_text in answer_key[question_text]:
                            answer[0].wait_for(state="visible")
                            page.wait_for_timeout(1000)
                            answer[0].click()
                            correct_answer_found = True
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
                        page.wait_for_timeout(1000)
                        answer_choice[0][0].click()
                except Exception as e:
                    print(f"Error selecting correct answer: {e}")
                    browser.close()
                    return

                # Click the Next Question button
                try:
                    next_question_button = page.locator("button[id='nextQuestion']")
                    # Wait for both the fadeIn class AND visibility
                    page.wait_for_function(
                        """() => {
                            const button = document.getElementById('nextQuestion');
                            return button && 
                                button.classList.contains('fadeIn') && 
                                (button.style.visibility === 'visible' || getComputedStyle(button).visibility === 'visible');
                        }"""
                    )
                    page.wait_for_timeout(1000)
                    next_question_button.click()
                except Exception as e:
                    print(f"Error clicking Next Question button: {e}")
                    browser.close()
                    return
                quiz_question_count += 1

            # Claim rewards after completing all questions
            try:
                page.wait_for_load_state("networkidle")
                claim_rewards_button = page.locator("a[class*='kiaccountsbuttongreen']", has_text="CLAIM YOUR REWARD")
                claim_rewards_button.wait_for(state="visible")
                claim_rewards_button.click()
            except Exception as e:
                print(f"Error claiming rewards: {e}")
                timestamp = datetime.datetime.now().strftime("%m-%d_%H-%M-%S")
                filename = f"screenshot_{timestamp}.png"
                os.makedirs("../snapshots", exist_ok=True)
                page.screenshot(path=f'../snapshots/{filename}')
                browser.close()
                return
            
            # Handle reward iframe and log results
            try:
                page.wait_for_load_state("networkidle")
                page.wait_for_selector("iframe[id='jPopFrame_content']", state="visible")
                reward_iframe = page.frame_locator("iframe[id='jPopFrame_content']")
                reward_submit = reward_iframe.locator("a[id='submit'], a[class='buttonsubmit']")
                reward_submit.wait_for(state="visible")
                page.wait_for_timeout(1000)
                reward_submit.click()
            except Exception as e:
                print(f"Error handling reward iframe: {e}")
                return
            
            recaptcha_found = True
            # Check for reCAPTCHA popup
            try:
                recaptcha_iframe = reward_iframe.locator("iframe[title*='recaptcha']")
                recaptcha_iframe.wait_for(state="visible", timeout=5000)
                recaptcha_iframe = reward_iframe.frame_locator("iframe[title*='recaptcha']")
            except:
                #print("No reCAPTCHA challenge detected.")
                recaptcha_found = False
                pass
            
            # If recaptcha iframe was found...
            if recaptcha_found:
                recaptcha_solved = False
                reload_count = 0
                # If reCAPTCHA is found, switch to audio challenge
                try:
                    page.wait_for_timeout(2000)
                    audio_button = recaptcha_iframe.locator("button[id='recaptcha-audio-button']")
                    audio_button.wait_for(state="visible")
                    audio_button.click()
                    #print("reCAPTCHA challenge detected. Solving now...")
                except Exception as e:
                    print(f"Error trigger audio reCAPTCHA challenge: {e}")
                

                '''
                Attemping to solve the recaptcha, loop until page has reloaded 5 times.
                '''
                while recaptcha_solved == False:
                    # Press 'PLAY' button
                    try:
                        page.wait_for_timeout(2000)
                        audio_div = recaptcha_iframe.locator("div[class='rc-audiochallenge-control']")
                        play_audio_button = audio_div.locator("button", has_text="PLAY")
                        play_audio_button.wait_for(state="visible", timeout=5000)
                        play_audio_button.click()
                    except Exception as e:
                        # Indicates that reCAPTCHA detected automated queries, simply skips the quiz and adds a new quiz to the quiz_samples 
                        print(f"Error pressing PLAY button: {e}")
                        quiz_samples += all_quiz_titles[:1]
                        all_quiz_titles = all_quiz_titles[1:]
                        break
                    
                    # Get audio URL
                    try:
                        audio_source = audio_div.locator("audio[id='audio-source']")
                        audio_url = audio_source.get_attribute("src")
                    except Exception as e:
                        print(f"Error retrieving audio URL: {e}")
                        browser.close()
                        return
                    
                    # Transcribe audio using faster-whisper and enter it into the input area
                    try:
                        captcha_solution_text = transcribe_audio(audio_url)
                        captcha_input = recaptcha_iframe.locator("input[id='audio-response']")
                        #print(f"Transcribed audio: {captcha_solution_text}")
                        captcha_input.type(text=captcha_solution_text, delay=100)
                    except Exception as e:
                        print(f"Error inputting transcribed audio: {e}")
                        browser.close()
                        return

                    # Click the Verify button
                    try:
                        verify_button = recaptcha_iframe.locator("button[id='recaptcha-verify-button']")
                        verify_button.wait_for(state="visible")
                        verify_button.click()
                        #print("Submitted reCAPTCHA solution. Waiting for verification...")
                    except Exception as e:
                        print(f"Error clicking Verify button: {e}")
                        browser.close()
                        return
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
                        print("reCAPTCHA solved successfully.")
                        break
                
            # Log quiz results if 100% score not achieved
            try:
                page.wait_for_load_state("networkidle")
                quiz_score = page.locator("div[class*='quizScore']")
                quiz_score.wait_for(state="visible")
                quiz_score = quiz_score.inner_text().strip()
                if quiz_score != "100%":
                    os.makedirs("../logs", exist_ok=True)
                    with open("../logs/quiz_log.txt", "a", encoding="utf-8") as log_file:
                        log_file.write(f"Quiz '{title}' completed with score: {quiz_score}\n\n")
                        show_answers = page.locator("a", has_text="See correct answers!")
                        show_answers.wait_for(state="visible")
                        show_answers.click()
                        quiz_results = page.locator("div[id='quizResults']")
                        quiz_results.wait_for(state="visible")
                        log_file.write(f"{quiz_results.inner_text()}\n\n")
                print(f"Quiz '{title}' completed with score: {quiz_score}")
            except Exception as e:
                print(f"Error logging quiz results: {e}")
                timestamp = datetime.datetime.now().strftime("%m-%d_%H-%M-%S")
                filename = f"screenshot_{timestamp}.png"
                os.makedirs("../snapshots", exist_ok=True)
                page.screenshot(path=f'../snapshots/{filename}')
                continue            
            
        browser.close()
if __name__ == "__main__":
    main()