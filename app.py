from flask import Flask, session, request, redirect
from os import environ
import uuid
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = environ.get("FLASK_SECRET_KEY")


@app.route('/')
def index():  # put application's code here
    """
    index
    """
    return 'main page'


@app.route('/auth')
def auth_handler():
    """
    auth
    """
    return request.query_string


@app.route('/initiate-auth')
def auth_initiator():
    """
    init auth
    """
    params = make_url_params()
    return redirect(f"https://www.tumblr.com/oauth2/authorize?{urlencode(params)}")


if __name__ == '__main__':
    app.run()


def make_url_params(writeable: bool = False):
    scope = 'basic write' if writeable else 'basic'
    state = uuid.uuid4()
    session['state'] = state
    params = {
        'response_type': 'code',
        'client_id': environ.get('TUMBLR_CONSUMER_KEY'),
        'redirect_uri': environ.get('REDIRECT_URI'),
        'scope': scope,
        'approval_prompt': 'auto',
        'state': state,
    }
    return params
