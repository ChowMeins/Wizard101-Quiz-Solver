import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import json, os, time, sys, requests
import whisper
import logging

def logError(driver: WebDriver, errorMsg: str, errorComponent: str, exit: bool):
    os.makedirs('errors', exist_ok=True) # Ensure that directory 'screenshots' exists, otherwise create it
    logger = logging.getLogger()
    logger.error(errorMsg)
    screenshotName = f'errors/{errorComponent}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    driver.get_screenshot_as_file(screenshotName)
    if (exit):
        sys.exit(1)

    
def sendKeysAtIntervals(element: WebElement, input: str, interval: float) -> None:
    for char in input:
        element.send_keys(char)
        time.sleep(interval)

def wizLogin(driver: WebDriver) -> None: # Locate buttons and enter text needed to login
    wait = WebDriverWait(driver, 60)

    # Enter username
    try:
        login = wait.until(EC.presence_of_element_located((By.ID, 'loginUserName')))
        login.send_keys(os.getenv("WIZ_USERNAME"))
        #sendKeysAtIntervals(login, os.getenv("WIZ_USERNAME"), 0)
    except:
        logError(driver=driver, errorMsg='Username element not found.', errorComponent='username', exit=True)
    
    # Enter password
    try:
        password = wait.until(EC.presence_of_element_located((By.ID, 'loginPassword')))
        password.send_keys(os.getenv("WIZ_PASSWORD"))
        #sendKeysAtIntervals(password, os.getenv("WIZ_PASSWORD"), 0.0)
    except:
        logError(driver=driver, errorMsg='Password element not found.', errorComponent='password', exit=True)

    # Press login button
    try:
        loginButton = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'wizardButtonInput')))
        loginButton.click()
    except:
        logError(driver=driver, errorMsg='Login button element not found.', errorComponent='loginButton', exit=True)
    # Check to see if user has successfully logged in
    try:
        username = driver.find_element(By.ID, "userNameOverflow")
        print("Successfully logged in:", username.text)
    except:
        logError(driver=driver, errorMsg='Account not logged in succesfully', errorComponent='userName', exit=True)
        
    # FOR RECAPTCHA:
    # See if reCAPTCHA frame shows up
    try:
        wizPopupFrame = driver.find_element(By.ID, 'jPopFrame_content')
        driver.switch_to.frame(wizPopupFrame)
        loginRecaptchaPresent = True
    except:
        logError(driver=driver, errorMsg='No login reCAPTCHA found', errorComponent='loginCAPTCHA', exit=False)
        loginRecaptchaPresent = False
    # Switch to reCAPTCHA frame
    if loginRecaptchaPresent:
        frames = wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, 'iframe')))
        for frame in frames:
            #print('Pre Verification Frame', frame.get_attribute('title'), frame.get_attribute('id'))
            if frame.get_attribute('title') == 'reCAPTCHA':
                driver.switch_to.frame(frame)
                # Check the verify checkbox
                try:
                    verifyButton = wait.until(EC.presence_of_element_located((By.ID, 'recaptcha-anchor')))
                    verifyButton.click()
                except:
                    logError(driver=driver, errorMsg='Verify checkbox not found.', errorComponent='verifyLoginCheckBox', exit=False)
                # Click the audio button
                try:
                    frames = driver.find_elements(By.TAG_NAME, 'iframe')
                    audioButton = wait.until(EC.presence_of_element_located((By.ID, 'recaptcha-audio-button')))
                    audioButton.click()
                except:
                    logError(driver=driver, errorMsg='No audio button for login verification found.', errorComponent='verifyLoginAudio', exit=False)
                # Switch back to login frame
                try:
                    driver.switch_to.default_content()
                    wizPopupFrame = driver.find_elements(By.TAG_NAME, 'iframe')
                    for frame in wizPopupFrame:
                        print(len(wizPopupFrame))
                    driver.switch_to.frame(wizPopupFrame)
                except:
                    logError(driver=driver, errorMsg='Error when switching from verify frame to wizard popup frame', errorComponent='verifyLoginFrame', exit=False)
                # Confirm login
                try:
                    verifyLogin = wait.until(EC.presence_of_element_located((By.ID, 'bp_login')))
                    verifyLogin.click()
                except:
                    logError(driver=driver, errorMsg='Verify login not found.', errorComponent='verifyLogin', exit=False)


def loadTrivia(driver: WebDriver, questions: dict) -> None:
    with open("quizzes.json", "r") as file:
        data = json.load(file) # Load the quizzes.json file
        process_json(data, questions)
        

def process_json(data: dict, questions: dict) -> None: # Data loaded from json file is type dict
    for key, value in data.items():
        questions[key] = value

def navigateTrivia(driver: WebDriver, questions: dict, numSolved: int) -> None:
    for key in questions:
        if (numSolved >= 10):
            break
        triviaName = key
        triviaName = triviaName.lower().replace(' ', '-')
        url = 'https://www.wizard101.com/quiz/trivia/game/' + triviaName + '-trivia'
        driver.get(url)
        try:
            comeTomorrowText = driver.find_element(By.XPATH, "//*[@id='quizFormComponent']/div[2]/div/h2")
            if (comeTomorrowText):
                print("Quiz already solved. Proceeding to next quiz.")
                numSolved += 1
                continue
        except:
            print('No \"Come Back Tomorrow\" text found, proceeding to next quiz.')
            print(f'Number of Quizzes solved: {numSolved}')
            solveQuestions(driver, questions, key, numSolved)
            numSolved += 1

def solveQuestions(driver: WebDriver, questions: dict, triviaName: str, numSolved: int) -> None:
    questionsSolved = 0
    wait = WebDriverWait(driver, 10)

    while(questionsSolved < 12): # Quizzes are each 12 questions
        # Wait for next question to fade in
        try:
            nextButton = wait.until(EC.element_to_be_clickable((By.ID, 'nextQuestion')))
        except:
            logError(driver=driver, errorMsg='Next button element not found.', errorComponent='nextButton', exit=True)

        # Load question and answers from the webpage
        try:
            quizQuestion = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'quizQuestion')))
            answerDivs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.answer.fadeIn')))
            qa_pairs = questions.get(triviaName) # Loads qa pairs with a list of elements: [question, answer] from .json file
        except:
            logError(driver=driver, errorMsg='Question/Answer elements not found.', errorComponent='QA', exit=True)

        # Check if question/answer pair exists in dictionary
        if qa_pairs == None:
            logError(driver=driver, errorMsg='Question not found', errorComponent='newQA')
        else:
            possible_answers = [] # If correct answer choice matches, append answer text to possible_answers (multiple question may have same answer)
            for pair in qa_pairs:
                if quizQuestion.text == pair[0]:
                    possible_answers.append(pair[1])
            
            answerChoices = []
            correctAnswerFound = False

            for a in possible_answers:
                for answer in answerDivs: # answers is the 4 divs that include the answers that appears on the webpage
                    try:
                        answerText = answer.find_element(By.CLASS_NAME, 'answerText')
                        answerChoices.append(answerText.text)
                        answerBox = answer.find_element(By.CLASS_NAME, 'largecheckbox')
                        if(answer.text in possible_answers):
                            answerBox.click()
                            nextButton.click()
                            questionsSolved += 1
                            correctAnswerFound = True
                            print(f'Question #{questionsSolved} solved!')
                            break
                    except:
                        logError(driver=driver, errorMsg='Answer checkbox not found', errorComponent='answer', exit=True)
                if (correctAnswerFound):
                    break

                if (correctAnswerFound == False):
                    question = quizQuestion.text
                    answerString = ''
                    for a in answerChoices:
                        answerString += f'{a}, '
                    logError(driver=driver, errorMsg=f'Non-matching answer found: {question} : {answerString.rstrip(", ")}', exit=True)

    # Claim reward
    try:
        claimRewardFirstButton = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "CLAIM YOUR REWARD")))
        claimRewardFirstButton.click() # Opens up jpopFrame_content frame
    except:
        logError(driver=driver, errorMsg='First claim reward button not found.', errorComponent='rewardButton1st', exit=True)

    driver.switch_to.frame('jPopFrame_content')
    claimRewardFinalButton = wait.until(EC.element_to_be_clickable((By.ID, "submit")))
    claimRewardFinalButton.click()
    try:
        driver.switch_to.default_content()
        takeAnotherQuizBtn = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.LINK_TEXT, 'TAKE ANOTHER QUIZ!')))
        print(takeAnotherQuizBtn.text)
    except:
        solveCaptcha(driver)

def solveCaptcha(driver: WebDriver):
    wait = WebDriverWait(driver, 10)
    try:
        recaptchaWait = WebDriverWait(driver, 5)
        # Switch the jpopFrame
        wiz_frames = driver.find_elements(By.TAG_NAME, 'iframe')
        for frame in wiz_frames:
            #print(frame.get_attribute('id'))
            if frame.get_attribute('id') == 'jPopFrame_content':
                driver.switch_to.frame(frame)
                #print(f'switched to {id} frame.')
                break
        # Switch to recaptcha frame
        recaptcha_frames = driver.find_elements(By.TAG_NAME, 'iframe')
        for frame in recaptcha_frames:
            titleName = frame.get_attribute('title')
            if titleName == 'recaptcha challenge expires in two minutes':
                driver.switch_to.frame(frame)
                #print(f'switched to {titleName} frame.')
                break
        # Click the headphone logo to switch to an aural challenge
        audioChallenge = recaptchaWait.until(EC.element_to_be_clickable((By.ID, 'recaptcha-audio-button')))
        audioChallenge.click()
        #print('audio challenge started')
    except: 
        logError(driver=driver, errorMsg='reCAPTCHA audio button not found.', errorComponent='recaptchaButton', exit=True)
    try:
        playAudioButton = recaptchaWait.until(EC.presence_of_element_located((By.ID, ':2')))
        playAudioButton.click()
        #print('play audio')
    except:
        dom = driver.execute_script("return document.documentElement.outerHTML;")
    
    # Save the DOM to a text file
        with open("dom_output.html", "w", encoding="utf-8") as file:
            file.write(dom)
    
        #print("DOM has been saved to dom_output.html")
        logError(driver=driver, errorMsg='reCAPTCHA play button not found.', errorComponent='recaptchaPlay', exit=True)
    try:   
        audioElement = recaptchaWait.until(EC.presence_of_element_located((By.ID, 'audio-source')))
        audioUrl = audioElement.get_attribute('src')
        downloadMP3(audioUrl)
        #print('downloading mp3')
        audioTranscribed = transcribeAudio('audio_captcha.mp3')
        #print('Translated audio:', audioTranscribed)
        audioInput = recaptchaWait.until(EC.presence_of_element_located((By.ID, 'audio-response')))
        sendKeysAtIntervals(audioInput, audioTranscribed, 0.025)
    except:
        logError(driver=driver, errorMsg='reCAPTCHA audio not processed successfully.', errorComponent='recaptchaAudio', exit=True)
    try:
        verifyButton = recaptchaWait.until(EC.element_to_be_clickable((By.ID, 'recaptcha-verify-button')))
        verifyButton.click()
        #print('verify button clicked')
    except:
        logError(driver=driver, errorMsg='reCAPTCHA verify button not found.', errorComponent='recaptchaVerify', exit=True)

    driver.switch_to.default_content()
    try:
        wait.until(EC.visibility_of_element_located((By.LINK_TEXT, 'TAKE ANOTHER QUIZ!')))
    except:
        dom = driver.execute_script("return document.documentElement.outerHTML;")
    
        # Save the DOM to a text file
        with open("dom_output.html", "w", encoding="utf-8") as file:
            file.write(dom)
        logError(driver=driver, errorMsg='\"Take Another Quiz!\" text not found. Rewards may have not been claimed.', errorComponent='takeAnotherQuiz', exit=False)
    time.sleep(1)

def downloadMP3(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        with open('audio_captcha.mp3', 'wb') as file:
            file.write(response.content)
        print('Audio CAPTCHA successfully downloaded.')

def transcribeAudio(file: str) -> str:
    model = whisper.load_model("base")
    result = model.transcribe(audio='./audio_captcha.mp3')
    return result['text'].lower().rstrip('.') # Make transcribed text lowercase and remove period at end of sentence if present

def main():
    os.makedirs('errors', exist_ok=True)
    logging.basicConfig(filename='errors/error.log', 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        level=logging.ERROR,)
    load_dotenv(override=True) # Load env variables from .env file
    questions_map = {}
    
    chromeOptions = Options()
    chromeOptions.add_argument("--incognito")
    #chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("--disable-gpu")
    chromeOptions.add_argument("--mute-audio")
    chromeOptions.add_argument("--user-agent=user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    

    #chromeService = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(options=chromeOptions)

    driver.get("https://www.wizard101.com/game/trivia")
    driver.maximize_window()
    wizLogin(driver)
    loadTrivia(driver, questions_map)
    navigateTrivia(driver, questions_map, 0)
    driver.quit()

if __name__ == '__main__':
    main()
    print("Maximum daily quizzes taken. Closing program...")
    os.remove('audio_captcha.mp3')
    sys.exit(0)