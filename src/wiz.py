import random
from playwright.sync_api import sync_playwright
import time
import json
from collections import defaultdict
import os
from dotenv import load_dotenv
from transcribe import transcribe_audio

def main():
    load_dotenv()
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
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
        
        # Navigate to Earn Crowns page
        try:
            earn_crowns_tab = page.locator("a[id='earnCrownsLink']")
            earn_crowns_tab.wait_for(state="visible")
            earn_crowns_tab.click()
        except Exception as e:
            print(f"Error navigating to Earn Crowns tab: {e}")
            browser.close()
            return

        # Navigate to Play Trivia page
        try:
            play_trivia_link = page.locator("a[id='playTrivia']")
            play_trivia_link.wait_for(state="visible")
            play_trivia_link.click()
        except Exception as e:
            print(f"Error clicking Play Trivia link: {e}")
            browser.close()
            return
        
        with open("quizzes.json", "r") as f:
            quizzes = json.load(f)

        with open("nontrivia_urls.txt", "r") as f:
            nontrivia_urls = set(line.strip() for line in f.readlines() if line.strip())

        for title in random.sample(list(quizzes.keys()), 10):   
            # Load each quiz
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
            
            # Answer the 12 questions in the quiz
            for i in range(1, 13):
                # Parse question text
                try:
                    question_text = page.locator("div[class='quizQuestion']")
                    question_text.wait_for(state="visible")
                    question_text = question_text.inner_text().strip()
                    #print(f"Question #{i}: {question_text}")
                except Exception as e:
                    print(f"Error parsing question text: {e}")
                    browser.close()
                    return
                # Parse each answer choice
                try:
                    answer_container = page.locator("div[class='answersContainer']")
                    answer_choice = answer_container.locator("div[class*='answer']").all()
                    answer_choice = [[answer.locator("span[class='answerBox']"), answer.locator("span[class='answerText']")] for answer in answer_choice]
                    correct_answer_found = False
                    correct_answer_text = ""
                except Exception as e:
                    print(f"Error parsing answer choices: {e}")
                    browser.close()
                    return
                # Select the correct answer if it exists in the answer key
                try:
                    #print("Answer choices:")
                    for answer in answer_choice:
                        answer[1].wait_for(state="visible")
                        answer_text = answer[1].inner_text().strip()
                        #print(f"- {answer_text}")
                        if answer_text in answer_key[question_text]:
                            answer[0].wait_for(state="visible")
                            page.wait_for_timeout(1000)
                            answer[0].click()
                            correct_answer_found = True
                            correct_answer_text = answer_text
                    # Otherwise, select the first answer choice
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
                        #print(f"No correct answer found in the answer key. Choosing first answer choice: {answer_choice[0][1].inner_text()}.")
                    ##else:
                        #print(f"Correct answer found: {correct_answer_text}")
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
                    page.wait_for_timeout(500)
                    next_question_button.click()
                except Exception as e:
                    print(f"Error clicking Next Question button: {e}")
                    browser.close()
                    return
            # Claim rewards after completing 12 questions
            try:
                page.wait_for_load_state("networkidle")
                claim_rewards_button = page.locator("a[class*='kiaccountsbuttongreen']")
                claim_rewards_button.wait_for(state="visible")
                claim_rewards_button.click()
            except Exception as e:
                print(f"Error claiming rewards: {e}")
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
                browser.close()
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
            
            if recaptcha_found:
                recaptcha_solved = False
                # If reCAPTCHA is found, switch to audio challenge
                try:
                    page.wait_for_timeout(2000)
                    audio_button = recaptcha_iframe.locator("button[id='recaptcha-audio-button']")
                    audio_button.wait_for(state="visible")
                    audio_button.click()
                    #print("reCAPTCHA challenge detected. Solving now...")
                except Exception as e:
                    print(f"Error trigger audio reCAPTCHA challenge: {e}")

                while recaptcha_solved == False:
                    # Press 'PLAY' button
                    try:
                        page.wait_for_timeout(2000)
                        audio_div = recaptcha_iframe.locator("div[class='rc-audiochallenge-control']")
                        play_audio_button = audio_div.locator("button", has_text="PLAY")
                        play_audio_button.wait_for(state="visible", timeout=5000)
                        play_audio_button.click()
                    except Exception as e:
                        # Indicates that reCAPTCHA detected automated queries, reload to try and resolve the issue
                        print(f"Error pressing PLAY button: {e}")
                        page.reload()
                        continue
                    
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
            except Exception as e:
                print(f"Error logging quiz results: {e}")
                browser.close()
                return
            finally:
                print(f"Quiz '{title}' completed with score: {quiz_score}")

        


        
        # Keep the browser open for manual inspection
        
        browser.close()
if __name__ == "__main__":
    main()