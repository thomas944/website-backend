import base64
import random
import string
from datetime import datetime, timezone, timedelta

import requests
from decouple import config
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponseRedirect

# ====================== CONFIG ======================
CLIENT_ID = config('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = config('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = config('REDIRECT_URI')
STATE_KEY = 'spotify_auth_state'

# In-memory tokens — replace with session or DB storage
access_token = None
refresh_token = None
expires_in = None

# ====================== HELPERS ======================
def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# ====================== VIEWS ======================

@api_view(['GET'])
def login(request):
    state = generate_random_string(16)
    request.session[STATE_KEY] = state

    scopes = 'user-read-playback-state user-read-currently-playing user-read-recently-played user-read-email user-read-private'

    query_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'scope': scopes,
        'redirect_uri': REDIRECT_URI,
        'state': state
    }

    auth_url = f"https://accounts.spotify.com/authorize?{requests.compat.urlencode(query_params)}"
    return HttpResponseRedirect(auth_url)


@api_view(['GET'])
def callback(request):
    global access_token, refresh_token, expires_in

    code = request.query_params.get('code')
    state = request.query_params.get('state')
    stored_state = request.session.get(STATE_KEY)

    if not state or state != stored_state:
        return Response({'error': 'state_mismatch'}, status=status.HTTP_400_BAD_REQUEST)

    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    data = {
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    token_url = 'https://accounts.spotify.com/api/token'
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code != 200:
        return Response({'error': 'token exchange failed'}, status=response.status_code)

    token_data = response.json()
    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']
    expires_in = datetime.now(timezone.utc) + timedelta(seconds=token_data['expires_in'])

    user_info = requests.get(
        'https://api.spotify.com/v1/me',
        headers={'Authorization': f'Bearer {access_token}'}
    ).json()

    return Response({
        'message': 'Successfully Logged in',
        'userData': user_info,
        'accessToken': access_token,
        'refreshToken': refresh_token
    })


@api_view(['GET'])
def refresh_token_view(request):
    global access_token, expires_in

    if not refresh_token:
        return Response({'success': False, 'details': 'Please log in first'}, status=status.HTTP_401_UNAUTHORIZED)

    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Authorization': f'Basic {b64_auth_str}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post('https://accounts.spotify.com/api/token', data=data, headers=headers)
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = datetime.now(timezone.utc) + timedelta(seconds=token_data['expires_in'])

        return Response({
            'access_token': access_token,
            'expires_in': expires_in.isoformat()
        })
    else:
        return Response({'success': False, 'message': 'failed to refresh token'}, status=500)


@api_view(['GET'])
def status_view(request):
    global access_token, refresh_token, expires_in

    if not access_token or not refresh_token:
        return Response({'success': False, 'details': 'Please log in first'}, status=status.HTTP_401_UNAUTHORIZED)

    if datetime.now(timezone.utc) > expires_in:
        return refresh_token_view(request)

    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://api.spotify.com/v1/me/player/currently-playing', headers=headers)

    if response.status_code == 204:
        return Response({'success': True, 'online': False, 'track': None})

    if response.status_code != 200:
        return Response({'success': False, 'error': 'Failed to fetch status'}, status=response.status_code)

    data = response.json()
    track = {
        'name': data['item']['name'],
        'artists': [a['name'] for a in data['item']['artists']],
        'url': data['item']['external_urls']['spotify'],
        'image': next((i['url'] for i in data['item']['album']['images'] if i['height'] == 64), None),
    }

    return Response({
        'success': True,
        'online': data['is_playing'],
        'track': track
    })


@api_view(['GET'])
def testing(request):
    return Response({'success': True})


@api_view(['GET'])
def index(request):
    return Response({'message': 'Server is running. Go to /login to start.'})