from flask import (Flask, request, make_response, render_template, flash, g,
                   url_for, redirect, jsonify, abort, g)
from flask import session as cookie_session

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

import requests
import random
import string
import json
import time

from database_setup import Base, User, Category, Item

# Initialize the app object
app = Flask(__name__)

# Connect to the database and obtain a session object
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def int_time_now():
    """ Returns the time in seconds since the Unix epoch """
    return int(time.time())


def parse_query_string(query_string):
    """
    Returns a dictionary of query string parameters

    Used for parsing results from certain Facebook APIs that return results in
    a query string format.
    """

    parameters = query_string.split('&')
    result = {}

    for parameter in parameters:
        parameter_parts = parameter.split('=', 1)
        if len(parameter_parts) != 2:
            continue

        result[parameter_parts[0]] = parameter_parts[1]

    return result


def error_response(error, status):
    """ Returns a JSON response containing an error string and status """
    return (jsonify({'error': error}), status)


def read_json(filename):
    """ Reads JSON from a file """
    f = open(filename)
    result = json.loads(f.read())
    f.close()
    return result


# DB interaction tools
def get_user_by_email(email):
    """ Gets a user object by the unique email key """
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except:
        # The specified user could not be found
        return None


def get_user_by_id(id):
    """ Get user by the ID in the database """
    return session.query(User).filter_by(id=id).one()


def create_user(email, name, picture):
    """ Creates a new user """
    new_user = User(email=email, name=name, picture=picture)
    session.add(new_user)
    session.commit()
    return new_user


# Used in the OAuth processes
GOOGLE_CLIENT_ID = read_json('google_client_secrets.json')['web']['client_id']
FACEBOOK_APP_DATA = read_json('facebook_client_secrets.json')


@app.before_request
def before_request():
    """ Sets logged_in and user_id onto Flask's g object for convenience """
    g.logged_in = cookie_session.get('email') is not None
    g.user_id = cookie_session.get('user_id')


@app.route('/api/categories.json')
def catalog_json():
    """ JSON API for accessing all categories """
    categories = session.query(Category).all()
    return jsonify(categories=[x.serialize for x in categories])


@app.route('/api/category/<int:category_id>.json')
def category_json(category_id):
    """ JSON API for accessing a specific category and its items """
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except:
        return abort(404)

    items = session.query(Item).filter_by(category_id=category_id).all()

    items_dict = [item.serialize for item in items]
    category_dict = category.serialize
    category_dict['items'] = items_dict

    return jsonify(category=category_dict)


@app.route('/api/item/<int:item_id>.json')
def item_json(item_id):
    """ JSON API for accessing a specific item """
    try:
        item = session.query(Item).filter_by(id=item_id).one()
    except:
        return abort(404)

    return jsonify(item=item.serialize)


@app.route('/category/')
@app.route('/')
def index():
    """ Returns home page with category list and 10 newest items """

    categories = session.query(Category).order_by(desc(Category.id)).all()
    latest_items = session.query(Item).order_by(desc(Item.id)).limit(10).all()
    return render_template('categories.html', categories=categories,
                           items=latest_items)


@app.route('/category/new', methods=['GET', 'POST'])
def create_category():
    """ Creates a category for a given user if logged in """
    # Check login via session email
    if not g.logged_in:
        return abort(401)

    if request.method == 'GET':
        return render_template('create_category.html')
    elif request.method == 'POST':
        category_name = request.form['name']
        new_category = Category(name=category_name, timestamp=int_time_now(),
                                user_id=g.user_id)

        session.add(new_category)
        session.commit()
        flash('Category "%s" created' % category_name)

    return redirect(url_for('index'))


@app.route('/category/<int:category_id>')
def show_category(category_id):
    """
    Shows a category and its items. Options for editing and deleting are shown
    if the user is logged in and matches the user id of a given category.
    """
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except:
        return abort(404)

    items = session.query(Item).filter_by(category=category).all()
    can_edit = g.logged_in and category.user_id == g.user_id

    return render_template('show_category.html', category=category,
                           can_edit=can_edit, items=items)


@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    """
    Enables editing of a category if the user is logged in and matches the user
    id of a given category.
    """
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except:
        return abort(404)

    if (not g.logged_in) or (category.user_id != g.user_id):
        return abort(401)

    if request.method == 'GET':
        return render_template('edit_category.html',
                               category=category)
    elif request.method == 'POST':
        category.name = request.form['name']
        session.add(category)
        session.commit()
        flash('Category "%s" edited' % category.name)
        return redirect(url_for('index'))


@app.route('/category/<int:category_id>/delete', methods=['GET', 'POST'])
def delete_category(category_id):
    """
    Deletes a category with confirmation message if if the user is logged in
    and matches the user id of a given category.
    """
    try:
        category = session.query(Category).filter_by(id=category_id).one()
    except:
        return abort(404)

    if (not g.logged_in) or (category.user_id != g.user_id):
        return abort(401)

    if request.method == 'GET':
        return render_template('confirm_delete_category.html',
                               category=category)

    elif request.method == 'POST':
        category_name = category.name
        session.query(Item).filter_by(category_id=category.id).delete()
        session.query(Category).filter_by(id=category.id).delete()
        session.commit()
        flash('Category "%s" deleted' % category_name)
        return redirect(url_for('index'))


@app.route('/item/new', methods=['GET', 'POST'])
def create_item():
    """ Creates an item for a given in a given category user if logged in """

    if not g.logged_in:
        return abort(401)

    if request.method == 'GET':
        categories = session.query(Category).all()

        return render_template('create_item.html', categories=categories)

    elif request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category_id = int(request.form['category'])

        new_item = Item(name=name, description=description,
                        category_id=category_id, timestamp=int_time_now(),
                        user_id=cookie_session['user_id'])
        session.add(new_item)
        session.commit()
        flash('Item "%s" created' % name)
        return redirect(url_for('index'))


@app.route('/item/<int:item_id>')
def show_item(item_id):
    """
    Shows an item with its information. Options for editing and deleting are
    shown if the user is logged in and matches the user id of a given category.
    """
    try:
        item = session.query(Item).filter_by(id=item_id).one()
    except:
        return abort(404)

    can_edit = g.logged_in and (item.user_id == g.user_id)

    return render_template('show_item.html', item=item, can_edit=can_edit)


@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    """
    Enables editing of an item and changing category if the user is logged in
    and matches the user id of a given category.
    """
    try:
        item = session.query(Item).filter_by(id=item_id).one()
    except:
        return abort(404)

    if (not g.logged_in) or (item.user_id != g.user_id):
        return abort(401)

    if request.method == 'GET':
        # PEP8 complains about E712 here but that cannot be avoided due to
        # the overloaded != operator
        categories = session.query(Category).all()

        return render_template('edit_item.html', categories=categories,
                               item=item)

    elif request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        item.category_id = int(request.form['category'])

        session.add(item)
        session.commit()
        flash('Item "%s" edited' % item.name)
        return redirect(url_for('show_item', item_id=item.id))


@app.route('/item/<int:item_id>/delete', methods=['GET', 'POST'])
def delete_item(item_id):
    """
    Deletes a category with confirmation message if if the user is logged in
    and matches the user id of a given category.
    """
    try:
        item = session.query(Item).filter_by(id=item_id).one()
    except:
        return abort(404)

    if (not g.logged_in) or (item.user_id != g.user_id):
        return abort(401)

    if request.method == 'GET':
        return render_template('confirm_delete_item.html', item=item)

    elif request.method == 'POST':
        item_name = item.name
        session.query(Item).filter_by(id=item_id).delete()
        session.commit()
        flash('Item "%s" deleted' % item_name)
        return redirect(url_for('index'))


@app.route('/login')
def login():
    """ Sets a state and presents Google and Facebook login options """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))

    cookie_session['state'] = state
    return render_template('login.html', state=state,
                           google_client_id=GOOGLE_CLIENT_ID,
                           facebook_app_id=FACEBOOK_APP_DATA['web']['app_id'])


@app.route('/auth/gconnect', methods=['POST'])
def google_login():
    """ Handler used by ajax call to initiate Google OAuth login process """
    # Validate state token
    if request.args.get('state') != cookie_session['state']:
        return error_response('Invalid state parameter', 401)

    auth_code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('google_client_secrets.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(auth_code)
    except FlowExchangeError:
        return error_response('Failed to upgrade authorization code', 401)

    access_token = credentials.access_token

    result = requests.get('https://www.googleapis.com/oauth2/v1/tokeninfo',
                          params=dict(access_token=access_token)).json()

    if result.get('error') is not None:
        return error_response(result['error'], 500)

    # Verify access token is used for intended user
    gplus_id = credentials.id_token['sub']

    if result['user_id'] != gplus_id:
        return error_response('Token\'s user ID does not match given ID', 401)

    if result['issued_to'] != GOOGLE_CLIENT_ID:
        return error_response('Token\'s client ID does not match app\'s', 401)

    stored_access_token = cookie_session.get('access_token')
    stored_gplus_id = cookie_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        return jsonify({'message': 'Already connected'})

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

    cookie_session['user_id'] = user_id

    flash('Google login successful')

    return jsonify({'message': 'Google login successful'})


@app.route('/auth/fbconnect', methods=['POST'])
def facebook_login():
    """ Handler used by ajax call to initiate Facebook OAuth login process """

    if request.args.get('state') != cookie_session['state']:
        return error_response('Invalid state parameter', 401)

    access_token = request.data
    app_id = FACEBOOK_APP_DATA['web']['app_id']
    app_secret = FACEBOOK_APP_DATA['web']['app_secret']

    result = requests.get('https://graph.facebook.com/oauth/access_token',
                          params=dict(grant_type='fb_exchange_token',
                                      client_id=app_id,
                                      client_secret=app_secret,
                                      fb_exchange_token=access_token)).text

    token = parse_query_string(result)['access_token']

    data = requests.get('https://graph.facebook.com/v2.5/me?',
                        params=dict(access_token=token,
                                    fields='name,id,email')).json()

    cookie_session['provider'] = 'facebook'

    username = data['name']
    email = data['email']

    cookie_session['facebook_id'] = data['id']
    cookie_session['access_token'] = token

    url = ('https://graph.facebook.com/v2.5/me/picture?%s&redirect=0'
           '&height=200&width=200') % token
    data = requests.get('https://graph.facebook.com/v2.5/me/picture',
                        params=dict(redirect=0, height=200, width=200,
                                    access_token=token)).json()

    picture = data['data']['url']

    # see if user exists
    user = get_user_by_email(email)

    if not user:
        user = create_user(email, username, picture)

    cookie_session['user_id'] = user.id
    cookie_session['email'] = email

    flash('Facebook login successful')
    return jsonify({'message': 'Facebook login successful'})


def google_logout():
    """ Log out from a Google third-party login """
    access_token = cookie_session.get('access_token')
    if access_token is None:
        # User is not logged in
        return

    del cookie_session['gplus_id']
    del cookie_session['access_token']

    result = requests.get('https://accounts.google.com/o/oauth2/revoke',
                          params=dict(token=access_token))

    # Invalid token should be ignored since that usually means the user is
    # already logged out
    if result.status_code != 200 \
            and json.loads(result[1])['error'] != 'invalid_token':
        return error_response('Failed to revoke token for user', 400)


def facebook_logout():
    """ Log out from a Facebook third-party login """
    facebook_id = cookie_session.get('facebook_id')
    access_token = cookie_session.get('access_token')

    requests.delete('https://graph.facebook.com/%s/permissions' % facebook_id,
                    params=dict(access_token=access_token))


@app.route('/logout')
def logout():
    """
    A generic logout url that detects the third-party OAuth provider and calls
    respective logout functions
    """
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
        del cookie_session['user_id']
        del cookie_session['provider']
        flash('You have been successfully logged out')

    else:
        flash('You were not logged in')
    return redirect(url_for('index'))

# Place at end of file
if __name__ == '__main__':
    # Start Flask server

    # Set to False in production
    app.debug = True
    key = 'Replace this key with a better one in production'
    app.secret_key = key
    app.run(host="0.0.0.0", port=5000)
