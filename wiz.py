from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import json, os, time, sys

def wizLogin(driver: WebDriver) -> None: # Locate buttons and enter text needed to login
    login = driver.find_element(By.ID, 'loginUserName')
    password = driver.find_element(By.ID, 'loginPassword')
    loginButton = driver.find_element(By.CLASS_NAME, 'wizardButtonInput')
    login.send_keys(os.getenv("WIZ_USERNAME"))
    password.send_keys(os.getenv("WIZ_PASSWORD"))
    loginButton.click()

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
            print(f"Exception type: {type(e)}")
            print(f"Exception message: {e}")
            print(f'Number of Quizzes solved: {numSolved}')
            solveQuestions(driver, questions, key, numSolved)
            numSolved += 1

def solveQuestions(driver: WebDriver, questions: dict, triviaName: str, numSolved: int) -> None:
    questionsSolved = 0
    while(questionsSolved < 12):
        wait = WebDriverWait(driver, 300)
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
        for answer in possible_answers:
                for answerDiv in answers:
                    answerText = answerDiv.find_element(By.CLASS_NAME, 'answerText')
                    answerChoices.append(answerText.text)
                    answerBox = answerDiv.find_element(By.CLASS_NAME, 'largecheckbox')
                    if(answerText.text in possible_answers):
                        answerBox.click()
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

        
    claimRewardFirstButton = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "CLAIM YOUR REWARD")))
    claimRewardFirstButton.click()
    driver.switch_to.frame('jPopFrame_content')
    claimRewardFinalButton = wait.until(EC.element_to_be_clickable((By.ID, "submit")))
    claimRewardFinalButton.click()
    driver.switch_to.default_content()
    nextQuiz = wait.until(EC.visibility_of_element_located((By.LINK_TEXT, 'TAKE ANOTHER QUIZ!')))
    time.sleep(1)


def main():
    load_dotenv() # Load env variables from .env file
    questions_map = {}

    driver = webdriver.Chrome()
    driver.get("https://www.wizard101.com/game/trivia")
    wizLogin(driver)
    loadTrivia(driver, questions_map)
    navigateTrivia(driver, questions_map, 0)
    driver.quit()

if __name__ == '__main__':
    main()
    print("Maximum daily quizzes taken. Closing program...")
    sys.exit(0)