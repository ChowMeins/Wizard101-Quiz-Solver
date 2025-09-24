"""
Custom exceptions for the QuizBot application.
"""

class QuizBotException(Exception):
    """Base exception class for all QuizBot related errors"""
    pass

class FileLoadingException(QuizBotException):
    "Raised when loading the .json file is either not found or has a syntax error in the file."
    pass

class RecaptchaFailedException(QuizBotException):
    """
    Raised when reCAPTCHA fails due to bot detection or multiple failed attempts.
    This typically requires browser restart and retry with a different quiz.
    """
    pass

class QuizProcessingException(QuizBotException):
    """
    Raised when there's a technical error processing the quiz (timeouts, element not found, etc.)
    These errors usually don't require browser restart.
    """
    pass

class LoginException(QuizBotException):
    """
    Raised when login fails due to invalid credentials or website issues.
    """
    pass

class NavigationException(QuizBotException):
    """
    Raised when navigation to quiz URL fails or quiz page doesn't load properly.
    """
    pass

class QuizCompletedException(QuizBotException):
    """
    Raised when attempting to take a quiz that has already been completed today.
    This is more of a flow control exception than an error.
    """
    pass