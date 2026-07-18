import re

CELLPHONE_PATTERN = re.compile(r'^\+51 9\d{8}$')
USERNAME_PATTERN = re.compile(r'^[a-z][a-z0-9]*$')
PASSWORD_PATTERN = re.compile(r'^[a-zA-Z0-9]{8,50}$')
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
MAX_LENGTH = 250
MAX_USERNAME_LENGTH = 50
NAME_PATTERN = re.compile(r'^[a-záéíóúñü]+( [a-záéíóúñü]+)*$')

PASSWORD_RESET_CODE_PATTERN = re.compile(r'^\d{6}$')
PASSWORD_RESET_CODE_TTL_MINUTES = 10
PASSWORD_RESET_MAX_VERIFICATION_ATTEMPTS = 3
PASSWORD_RESET_DAILY_LIMIT_HOURS = 24
PASSWORD_RESET_CODE_GENERATION_RETRIES = 5
