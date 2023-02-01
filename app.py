from flask import Flask, session
from dotenv import load_dotenv
from os import environ

load_dotenv(override=True)
app = Flask(__name__)
app.secret_key = environ.get("FLASK_SECRET_KEY")


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

if __name__ == '__main__':
    app.run()
