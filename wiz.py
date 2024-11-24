from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import json, os, time, sys, requests
import whisper
def sendKeysAtIntervals(element: WebElement, input: str, interval: float) -> None:
    for char in input:
        element.send_keys(char)
        time.sleep(interval)

def wizLogin(driver: WebDriver) -> None: # Locate buttons and enter text needed to login
    wait = WebDriverWait(driver, 300)
    try:
        login = wait.until(EC.presence_of_element_located((By.ID, 'loginUserName')))
        password = wait.until(EC.presence_of_element_located((By.ID, 'loginPassword')))
        loginButton = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'wizardButtonInput')))
        sendKeysAtIntervals(login, os.getenv("WIZ_USERNAME"), 0.025)
        sendKeysAtIntervals(password, os.getenv("WIZ_PASSWORD"), 0.025)
        time.sleep(0.5)
        loginButton.click()
    except Exception as e:
        print('Exception:', e)
        driver.get_screenshot_as_file("login_error.png")

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
        except Exception as e:
            print('No come back tomorrow text found. Proceed to next quiz')
            print(f'Number of Quizzes solved: {numSolved}')
            solveQuestions(driver, questions, key, numSolved)
            numSolved += 1

def solveQuestions(driver: WebDriver, questions: dict, triviaName: str, numSolved: int) -> None:
    questionsSolved = 0
    wait = WebDriverWait(driver, 10)
    while(questionsSolved < 12):
        try:
            nextButton = wait.until(EC.element_to_be_clickable((By.ID, 'nextQuestion')))
            quizQuestion = driver.find_element(By.CLASS_NAME, 'quizQuestion')
            answers = driver.find_elements(By.CSS_SELECTOR, '.answer.fadeIn')
            qa_pairs = questions.get(triviaName)
            possible_answers = []
            correctAnswerFound = False
            # If correct answer choice matches, append answer text to possible_answers (multiple question may have same answer)

            if qa_pairs == None:
                print('No QA Pairs Found')
            for pair in qa_pairs:
                if quizQuestion.text == pair[0]:
                    possible_answers.append(pair[1])
            answerChoices = []
            for _ in possible_answers:
                    for answerDiv in answers:
                        answerText = answerDiv.find_element(By.CLASS_NAME, 'answerText')
                        answerChoices.append(answerText.text)
                        answerBox = answerDiv.find_element(By.CLASS_NAME, 'largecheckbox')
                        if(answerText.text in possible_answers):
                            answerBox.click()
                            time.sleep(1)
                            nextButton.click()
                            questionsSolved += 1
                            correctAnswerFound = True
                            break
                    if (correctAnswerFound):
                        break
            if (correctAnswerFound == False):
                print(quizQuestion.text)
                for a in answerChoices:
                    print(a)
            print(f'Question #{questionsSolved} solved!')
        except:
            driver.get_screenshot_as_file('question_error.png')
            break

        
    claimRewardFirstButton = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "CLAIM YOUR REWARD")))
    claimRewardFirstButton.click()
    driver.switch_to.frame('jPopFrame_content')
    claimRewardFinalButton = wait.until(EC.element_to_be_clickable((By.ID, "submit")))
    claimRewardFinalButton.click()
    time.sleep(1)
    try:
        recaptchaWait = WebDriverWait(driver, 5)
        frames = driver.find_elements(By.TAG_NAME, 'iframe')
        #print(len(frames))
        for i in range(len(frames)):
            titleName = frames[i].get_attribute('title')
            if titleName == 'recaptcha challenge expires in two minutes':
                driver.switch_to.frame(frames[i])
        audioChallenge = recaptchaWait.until(EC.element_to_be_clickable((By.ID, 'recaptcha-audio-button')))
        audioChallenge.click()

        audioElement = recaptchaWait.until(EC.presence_of_element_located((By.ID, 'audio-source')))
        audioUrl = audioElement.get_attribute('src')
        downloadMP3(audioUrl)
        audioTranscribed = transcribeAudio('audio_captcha.mp3')
        #print('Translated audio:', audioTranscribed)
        audioInput = recaptchaWait.until(EC.presence_of_element_located((By.ID, 'audio-response')))
        sendKeysAtIntervals(audioInput, audioTranscribed, 0.025)
        verifyButton = recaptchaWait.until(EC.element_to_be_clickable((By.ID, 'recaptcha-verify-button')))
        verifyButton.click()
    except Exception as e:
        print(e)
        print('reCAPTCHA not found.')

    driver.switch_to.default_content()

    wait.until(EC.visibility_of_element_located((By.LINK_TEXT, 'TAKE ANOTHER QUIZ!')))

def downloadMP3(url: str):
    response = requests.get(url)
    if response.status_code == 200:
        with open('audio_captcha.mp3', 'wb') as file:
            file.write(response.content)
        print('Audio CAPTCHA successfully downloaded.')

def transcribeAudio(file: str) -> str:
    model = whisper.load_model("base")
    result = model.transcribe(audio='./audio_captcha.mp3')
    return result['text']

def main():
    load_dotenv(override=True) # Load env variables from .env file
    questions_map = {}
    
    chromeOptions = Options()
    chromeOptions.add_argument("--headless")
    chromeOptions.add_argument("--disable-gpu")
    chromeOptions.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=chromeOptions)
    driver.get("https://www.wizard101.com/game/trivia")
    wizLogin(driver)
    loadTrivia(driver, questions_map)
    navigateTrivia(driver, questions_map, 0)
    driver.quit()

if __name__ == '__main__':
    main()
    print("Maximum daily quizzes taken. Closing program...")
    sys.exit(0)