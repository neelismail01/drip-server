from flask import (
    Blueprint,
    current_app,
    redirect,
    session,
    url_for
)
from authlib.integrations.flask_client import OAuth

auth_blueprint = Blueprint('auth', __name__)

oauth = OAuth(current_app)
oauth.register(
    name='google',
    client_id="11431521918-3rdlae667bhfhl73p59rgceilve79ahm.apps.googleusercontent.com",
    client_secret="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",
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={ 'scope': 'openid email profile' }
)

@auth_blueprint.route('/')
def homepage():
    user = session.get('user')
    if user:
        return (
            "<p>Hello! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<a class="button" href="/logout">Logout</a>'
        )
    else:
        return '<a class="button" href="/login">Google Login</a>'


@auth_blueprint.route('/login')
def login():
    redirect_uri = url_for('auth.callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_blueprint.route('/callback')
def callback():
    token = oauth.google.authorize_access_token()
    email = token['userinfo']['email']
    name = token['userinfo']['name']
    db = current_app.mongo.drip

    # check if user already exists
    existing_user = db.users.find_one({'email': email})
    if existing_user:
        return 'User already exists', 200

    # insert user into users collection
    user = {
        'email': email,
        'name': name,
        'username': None,
        'phone_number': None,
        'profile_pic': None,
        'shopping_preference': None,
        'inbox': []
    }
    db.users.insert_one(user)
    session['user'] = token['userinfo']
    return 'User signed up', 200

@auth_blueprint.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')