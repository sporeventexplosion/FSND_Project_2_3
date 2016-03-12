from flask import (Flask, request, make_response, render_template, flash, g,
                   url_for, redirect)
from flask import session as cookie_session

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import requests
import httplib2
import random
import string
import json

from database_setup import Base, User, Category, Item

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def get_json_response(content, status=200):
    response = make_response(json.dumps(content), status)
    response.headers['Content-Type'] = 'application/json'
    return response


# A function that "packages" errors into a dictionary for easier client
# handling
def get_error_response(error, status):
    return get_json_response({'error': error}, status)


def http_request(url, method='GET'):
    return httplib2.Http().request(url, method)


def read_json(filename):
    f = open(filename)
    result = json.loads(f.read())
    f.close()
    return result


# DB interaction tools
def get_user_by_email(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        # The specified user could not be found
        return None


def get_user_by_id(id):
    return session.query(User).filter_by(id=id).one()


def create_user(email, name, picture):
    new_user = User(email=email, name=name, picture=picture)
    session.add(new_user)
    session.commit()
    return new_user


GOOGLE_CLIENT_ID = read_json('google_client_secrets.json')['web']['client_id']
FACEBOOK_APP_DATA = read_json('facebook_client_secrets.json')


@app.route('/')
def index():
    return render_template('root.html')


@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))

    cookie_session['state'] = state
    return render_template('login.html', state=state,
                           google_client_id=GOOGLE_CLIENT_ID,
                           facebook_app_id=FACEBOOK_APP_DATA['web']['app_id'])


@app.route('/auth/gconnect', methods=['POST'])
def google_login():
    # Validate state token
    if request.args.get('state') != cookie_session['state']:
        return get_error_response('Invalid state parameter', 401)

    auth_code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('google_client_secrets.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(auth_code)
    except FlowExchangeError:
        return get_error_response('Failed to upgrade authorization code', 401)

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)

    # Get response string, the second element of return tuple
    result = json.loads(http_request(url)[1])

    if result.get('error') is not None:
        return get_error_response(result['error'], 500)

    # Verify access token is used for intended user
    gplus_id = credentials.id_token['sub']

    if result['user_id'] != gplus_id:
        return get_error_response('Token\'s user ID does not match given ID',
                                  401)

    if result['issued_to'] != GOOGLE_CLIENT_ID:
        return get_error_response('Token\'s client ID does not match app\'s',
                                  401)

    stored_access_token = cookie_session.get('access_token')
    stored_gplus_id = cookie_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        return get_json_response({'message': 'Already connected'}, 200)

    # Store access_token and gplus_id in session cookie
    cookie_session['access_token'] = access_token
    cookie_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': access_token, 'alt': 'json'}
    data = requests.get(userinfo_url, params=params).json()

    # Only store what is needed to identify the user to avoid excessively
    # long cookies. The rest is stored in a database
    cookie_session['email'] = data['email']
    cookie_session['provider'] = 'google'

    user = get_user_by_email(data['email'])
    if not user:
        # Create a new user
        user_id = create_user(data['email'], data['name'], data['picture']).id
    else:
        user_id = user.id

    return get_json_response({'message': 'Google login successful'})


@app.route('/auth/fbconnect', methods=['POST'])
def facebook_login():
    if request.args.get('state') != cookie_session['state']:
        return get_error_response('Invalid state parameter', 401)

    access_token = request.data
    app_id = FACEBOOK_APP_DATA['web']['app_id']
    app_secret = FACEBOOK_APP_DATA['web']['app_secret']

    url = ('https://graph.facebook.com/oauth/access_token?grant_type='
           'fb_exchange_token&client_id=%s&client_secret=%s'
           '&fb_exchange_token=%s') % (app_id, app_secret, access_token)

    result = http_request(url)[1]

    userinfo_url = 'https://graph.facebook.com/v2.5/me'
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email' % token
    result = http_request(url)[1]

    data = json.loads(result)
    cookie_session['provider'] = 'facebook'

    username = data['name']
    email = data['email']

    cookie_session['facebook_id'] = data['id']

    cookie_session['access_token'] = token.split('=')[1]

    url = ('https://graph.facebook.com/v2.5/me/picture?%s&redirect=0'
           '&height=200&width=200') % token
    data = json.loads(http_request(url)[1])

    picture = data['data']['url']

    # see if user exists
    user = get_user_by_email(email)

    if not user:
        user = create_user(email, username, picture)

    cookie_session['user_id'] = user.id
    cookie_session['email'] = email

    flash('Facebook login successful')
    return get_json_response({'message': 'Facebook login successful'})


def google_logout():
    access_token = cookie_session.get('access_token')
    if access_token is None:
        # User is not logged in
        return

    url = ('https://accounts.google.com/o/oauth2/'
           'revoke?token=%s') % access_token
    result = http_request(url)

    del cookie_session['gplus_id']
    del cookie_session['access_token']

    # Invalid token should be ignored since that usually means the user is
    # already logged out
    if result[0]['status'] != '200' \
            and json.loads(result[1])['error'] != 'invalid_token':
        return get_error_response('Failed to revoke token for user', 400)


def facebook_logout():
    facebook_id = cookie_session.get('facebook_id')
    access_token = cookie_session.get('access_token')

    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
        % (facebook_id, access_token)

    http_request(url, 'DELETE')


@app.route('/logout')
def logout():
    if 'provider' in cookie_session:
        if cookie_session['provider'] == 'google':
            logout_result = google_logout()

            # Return the error for debugging
            if logout_result is not None:
                return logout_result

        elif cookie_session['provider'] == 'facebook':
            facebook_logout()
            del cookie_session['facebook_id']
        del cookie_session['email']
        del cookie_session['provider']
        flash('You have been successfully logged out')

    else:
        flash('You were not logged in')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Place at end of file
    app.debug = True
    # cryptographically secure random
    key = 'v6wQKajGHNkBIbUp8XOCrvbh8eHNaLceqIA3hXpgM7OHMgLBvPaVRcrIqyOutK_B'
    app.secret_key = key
    app.run(host="0.0.0.0", port=5000)
