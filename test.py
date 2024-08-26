from dotenv import load_dotenv
import os

# Explicitly specify the path to the .env file
load_dotenv(dotenv_path='.env')

# Now the environment variables should load
print(os.getenv('MAIL_SERVER'))
print(os.getenv('MAIL_PORT'))
print(os.getenv('MAIL_USERNAME'))
print(os.getenv('MAIL_PASSWORD'))
print(os.getenv('MAIL_USE_TLS'))
print(os.getenv('MAIL_USE_SSL'))
