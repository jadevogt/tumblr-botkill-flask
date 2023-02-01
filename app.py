from flask import Flask, session, request, redirect, render_template
from os import environ
import uuid
from urllib.parse import urlencode, urlparse, parse_qs
from base64 import b64encode
from json import dumps

from tumblr import Tumblr, RateLimitException

app = Flask(__name__)
app.secret_key = environ.get("FLASK_SECRET_KEY")


@app.route('/')
def index():
    """
    index
    """
    return 'click <a href="/initiate-auth">here</a> to initiate the authentication procedure'


@app.route("/list_blogs")
def list_blogs():
    try:
        tumblr = Tumblr(token=session.get("tumblr_token"))
        blog_list = tumblr.user_blogs()
        non_mutual_followers = []
        for blog in blog_list:
            followers = tumblr.blog_followers(blog)
            new = [f for f in followers if f["following"] != True]
            for follower in new:
                follower["follows"] = blog.name
            non_mutual_followers += new
        sus_blogs = {b.name: [] for b in blog_list}
        for follower in non_mutual_followers:
            info = tumblr.public_blog_post_count(blog_name=follower["name"])
            if info[0] == 0:
                follower["avatar"] = info[1]
                follower["report_json_str"] = dumps({
                    "post":None,
                    "urlreporting":f"https://www.tumblr.com/{follower['name']}",
                    "tumblelog":follower["name"],
                    "context":"blog"
                })
                sus_blogs[follower["follows"]].append(follower)
        return render_template("blog_list.html", blog_list=blog_list, sus_blogs=sus_blogs)
    except RateLimitException:
        return "<h1>application rate limit exceeded</h1><p>please try again later</p>"

@app.route('/auth')
def auth_handler():
    """
    auth
    """
    try:
        parsed_url = urlparse(request.url)
        qs = parse_qs(parsed_url.query)
        state = session.get("state")
        returned_state = qs.get("state")
        returned_code = qs.get("code")[0]
        tumblr = Tumblr()
        tumblr.authenticate(returned_code)
        session["tumblr_token"] = tumblr.token.to_dict()
        return f"""
        <h1>success!</h1>
        <a href="/list_blogs">list blogs</a>
        """
    except (RateLimitException, KeyError):
        return "<h1>application rate limit exceeded</h1><p>please try again later</p>"

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
