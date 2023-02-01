from flask import Flask, session, request, redirect
from os import environ
import uuid
from urllib.parse import urlencode, urlparse, parse_qs

from tumblr import Tumblr

app = Flask(__name__)
app.secret_key = environ.get("FLASK_SECRET_KEY")


@app.route('/')
def index():  # put application's code here
    """
    index
    """
    return 'main page'


@app.route('/check_auth')
def check_auth():
    tumblr = Tumblr(token=session.get("tumblr_token"))
    if tumblr.authenticated:
        return f"""
        authenticated: {tumblr.token}
        user info: {tumblr.user_info()}
        """
    else:
        return f"""
        not authenticated.
        """

@app.route("/list_blogs")
def list_blogs():
    tumblr = Tumblr(token=session.get("tumblr_token"))
    return "</br>".join(blog.__str__() for blog in tumblr.user_blogs())


@app.route('/auth')
def auth_handler():
    """
    auth
    """
    parsed_url = urlparse(request.url)
    qs = parse_qs(parsed_url.query)
    state = session.get("state")
    returned_state = qs.get("state")
    returned_code = qs.get("code")[0]
    tumblr = Tumblr()
    tumblr.authenticate(returned_code)
    session["tumblr_token"] = tumblr.token.to_dict()
    return f"""
    <h2>{tumblr.token}</h2>
    <h2>state: {state}</h2>
    <h2>returned state: {returned_state}</h2>
    """

@app.route('/initiate-auth')
def auth_initiator():
    """
    init auth
    """
    params = make_url_params(writeable=True)
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
