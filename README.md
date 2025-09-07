# **Wizard101 Quiz Solver**

> **Automated daily quiz solver for Wizard101 using AI-powered audio transcription**

An intelligent Python bot that automatically solves Wizard101's daily trivia quizzes to earn free crowns. Built with Playwright for web automation and Faster Whisper for audio captcha solving.

<img src="https://github.com/ChowMeins/Wizard101-Quiz-Solver/blob/main/Wizard101%20Trivia%20Webpage.png" width="75%" height="75%"/>

---

## **Features**

- **Fully Automated**: Handles login, navigation, and quiz solving
- **Audio Captcha Support**: Uses Faster Whisper AI to transcribe audio challenges
- **Docker Ready**: Complete containerized solution with docker-compose
- **Logging**: Tracks quiz results and saves incorrect answers for review
- **Modern Stack**: Built with Playwright (faster and more reliable than Selenium)

---

## **Tech Stack**

- **Web Automation**: [Playwright](https://playwright.dev/) - Modern browser automation
- **Audio Transcription**: [Faster Whisper](https://github.com/guillaumekln/faster-whisper) - Optimized OpenAI Whisper implementation
- **Containerization**: Docker & Docker Compose
- **Language**: Python 3.10.11

---

## **Quick Start with Docker**

### **Prerequisites**
- Docker and Docker Compose installed
- Wizard101 account credentials

### **Setup**

1. **Clone the repository**
   ```bash
   git clone https://github.com/ChowMeins/Wizard101-Quiz-Solver
   cd wizard101-quiz-solver
   ```

2. **Create environment file**
   > Do it manually, otherwise, you can do this
   ```bash
   echo "WIZ_USERNAME=your_username_here" > .env
   echo "WIZ_PASSWORD=your_password_here" >> .env
   ```

4. **Run with Docker**
   ```bash
   docker-compose up --build
   ```

The bot will automatically download the Whisper model, install dependencies, and start solving quizzes.

---

## **Local Installation**

### **Prerequisites**
```bash
pip install -r requirements.txt
playwright install firefox
```

### **Required packages**
- `playwright` - Web browser automation
- `faster-whisper` - AI audio transcription
- `requests` - HTTP requests handling
- `python-dotenv` - Environment variable management

### **Setup**
1. Create `.env` file with your credentials
2. Run: `python wiz.py`

---

## **Configuration**

### **Environment Variables**
```env
WIZ_USERNAME=your_wizard101_username
WIZ_PASSWORD=your_wizard101_password
```

### **Docker Features**
- **Headless Mode**: Runs with virtual display (xvfb)
- **Volume Mounting**: Live code updates during development

---

## **How It Works**

1. **Login**: Automatically logs into your Wizard101 account
2. **Navigation**: Finds and opens the daily quiz
3. **Question Solving**: Reads questions and selects answers
4. **Audio Captchas**: Transcribes audio challenges using AI
5. **Logging**: Records results and incorrect answers for learning

---

## **AI Audio Transcription**

The bot uses **Faster Whisper** (`distil-small.en` model) for audio captcha solving:
- **Faster**: Optimized for speed compared to standard Whisper
- **Accurate**: Specifically tuned for English audio
- **Efficient**: Lower memory usage and faster inference
- **Automatic**: Downloads model on first run

---

## **Limitations**

- **reCAPTCHA**: Visual captchas require manual intervention
- **Rate Limiting**: Respectful delays to avoid detection
- **Educational Purpose**: This project is for learning automation techniques

---

## **Troubleshooting**

### **Common Issues**
- **reCAPTCHA bot-detection**: reCAPTCHA may detected automated queries, and prevent audio challenges from being done. The current solution is reloading the page and trying again.
---

## **License**

This project is for educational purposes. Please respect Wizard101's Terms of Service.

---

## **Acknowledgments**

- [OpenAI Whisper](https://openai.com/research/whisper) - Speech recognition model
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) - Optimized implementation
- [Playwright](https://playwright.dev/) - Modern web automation framework
