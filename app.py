from flask import Flask, request, url_for, session, redirect, render_template
import spotipy
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import time
import os
from dotenv import load_dotenv

load_dotenv()

# initialising flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['SESSION_COOKIE_NAME'] = 'Tofuu Cookies'
TOKEN_INFO = 'token_info'

# initial welcome page
@app.route('/')
def welcome():
  return render_template('welcome.html')

# spotify's login screen
@app.route('/login')
def login():
  auth_url = create_spotify_oauth().get_authorize_url()
  return redirect(auth_url)

# where users go after authorisation by spotify
@app.route('/redirect')
def redirect_page():
  session.clear()
  error = request.args.get('error')
  if error:
    print(f"Authorization error: {error}")
    return redirect(url_for('welcome')) 
  code = request.args.get('code')
  token_info = create_spotify_oauth().get_access_token(code)
  session[TOKEN_INFO] = token_info
  return redirect(url_for('home', external = True))

# homepage
@app.route('/home')
def home():
  try:
    token_info = get_token()
  except:
    print("User not logged in")
    return redirect(url_for('login', _external = False))
  return render_template('home.html')

# logout page
@app.route('/logout')
def logout():
  session.clear()
  if os.path.exists(".cache"):
    os.remove(".cache")
    print("Logged out successfully")
  return redirect(url_for('welcome', _external = True))

# privacy policy
@app.route('/privacy')
def privacy():
  return render_template('privacy.html')

# about
@app.route('/about')
def about():
  return render_template('about.html')

# getting top items
@app.route('/<string:item_type>/<string:time_duration>')
def top_items(item_type, time_duration):
  items = get_top_items(item_type, time_duration)
  if item_type == 'tracks':
    songs = [
      {
        'name': track['name'], 
        'artist': ', '.join(artist['name'] for artist in track['artists']), 
        'duration': milli_to_min(track['duration_ms']),
        'image': track['album']['images'][0]['url']  
      }
      for track in items['items']
    ]
    return render_template('display.html', period=time_duration, songs=songs)
  
  elif item_type == 'artists':
    artists = [
      {
        'name': artist['name'], 
        'image': artist['images'][0]['url']
      }
      for artist in items['items']
    ]
    return render_template('displayArtist.html', period=time_duration, artists=artists)

# function for getting token
def get_token():
  token_info = session.get(TOKEN_INFO, None)
  if not token_info:
    raise Exception("User not logged in")

  # if token is expired, refresh
  now = int(time.time())
  is_expired = token_info['expires_at'] - now < 60
  if (is_expired):
    sp_oauth = create_spotify_oauth()
    token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
  return token_info

# function for creating oauth
def create_spotify_oauth():
  return SpotifyOAuth(
    client_id= os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret= os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri= url_for('redirect_page', _external=True),
    scope='user-top-read',
    show_dialog=True)
    
# function for getting items
def get_top_items(item_type, time_duration):
  try:
    token_info = get_token()
  except:
    print("User not logged in")
    return redirect(url_for('login', _external = False))
  
  sp = spotipy.Spotify(auth=token_info['access_token'])

  if item_type == 'tracks':
    return sp.current_user_top_tracks(limit = 10, offset = 0, time_range = time_duration)
  elif item_type == 'artists':
    return sp.current_user_top_artists(limit = 10, offset = 0, time_range = time_duration)

# function for converting song duration to minutes
def milli_to_min(duration):
  duration_seconds = duration // 1000
  minutes = duration_seconds // 60
  seconds = duration_seconds % 60
  if (seconds < 10):
    return str(minutes) + ':' + '0' + str(seconds)
  return str(minutes) + ':' + str(seconds)