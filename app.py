from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime
import concurrent.futures
import time

app = Flask(__name__)
headers = {
    "User-Agent": "Mozilla/5.0",  # Some servers block default Python agents
}

# Dictionary mapping Chess.com usernames to real names - UPDATE THIS WITH YOUR PLAYERS
CHESS_PLAYERS = {
    'chessbhaalu': 'Avneesh',
    'dshreyas0126': 'Shreyas Dangi',
    'hiral1239': 'Hiral',
    'chessboy2_0': 'Anay',
    'Medicore_name': 'Vansh Garg',
    'bitthal20': 'Bitthal',
    'shivamthakur94': 'Prithu Raj',
    'sushma_7': 'Sushma',
    'aastha_28': 'Aastha',
    'prakul2105': 'Prakul Balaji'
}

def get_player_data(username):
    """Fetch player profile and stats from Chess.com API"""
    try:
        # Get player profile
        profile_url = f"https://api.chess.com/pub/player/{username}"
        profile_response = requests.get(profile_url, headers=headers, timeout=10)
        
        if profile_response.status_code != 200:
            return None
            
        profile_data = profile_response.json()
        
        # Get player stats
        stats_url = f"https://api.chess.com/pub/player/{username}/stats"
        stats_response = requests.get(stats_url, headers=headers, timeout=10)
        
        if stats_response.status_code != 200:
            return None
            
        stats_data = stats_response.json()
        
        # Extract rapid rating
        rapid_rating = None
        if 'chess_rapid' in stats_data:
            rapid_rating = stats_data['chess_rapid'].get('last', {}).get('rating', 'N/A')
        
        # Get profile picture
        avatar = profile_data.get('avatar', 'https://www.chess.com/bundles/web/images/user-image.svg')
        
        # Use predefined real name if available, otherwise use API name
        display_name = CHESS_PLAYERS.get(username, profile_data.get('name', username))
        
        return {
            'username': username,
            'display_name': display_name,
            'rapid_rating': rapid_rating or 'N/A',
            'avatar': avatar,
            'country': profile_data.get('country', '').replace('https://api.chess.com/pub/country/', '').upper(),
            'title': profile_data.get('title', ''),
            'followers': profile_data.get('followers', 0),
            'last_online': profile_data.get('last_online', 0)
        }
        
    except Exception as e:
        print(f"Error fetching data for {username}: {e}")
        return None

def fetch_all_players_data():
    """Fetch data for all players concurrently"""
    players_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all requests
        future_to_username = {
            executor.submit(get_player_data, username): username 
            for username in CHESS_PLAYERS.keys()
        }
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_username):
            username = future_to_username[future]
            try:
                data = future.result()
                if data:
                    players_data.append(data)
            except Exception as e:
                print(f"Error processing {username}: {e}")
    
    # Sort players by rapid rating (highest first)
    players_data.sort(key=lambda x: x['rapid_rating'] if isinstance(x['rapid_rating'], int) else 0, reverse=True)
    
    return players_data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rapid')
def rapid():
    return render_template('rapid.html')

@app.route('/blitz')
def blitz():
    return render_template('blitz.html')

@app.route('/bullet')
def bullet():
    return render_template('bullet.html')

# Updated API endpoints for each format
@app.route('/api/players/rapid')
def get_rapid_players():
    """API endpoint to fetch rapid player data"""
    players_data = fetch_players_data('chess_rapid')
    return jsonify(players_data)

@app.route('/api/players/blitz')
def get_blitz_players():
    """API endpoint to fetch blitz player data"""
    players_data = fetch_players_data('chess_blitz')
    return jsonify(players_data)

@app.route('/api/players/bullet')
def get_bullet_players():
    """API endpoint to fetch bullet player data"""
    players_data = fetch_players_data('chess_bullet')
    return jsonify(players_data)

# Updated function to fetch specific format data
def fetch_players_data(format_type):
    """Fetch data for all players for a specific format"""
    players_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_username = {
            executor.submit(get_player_format_data, username, format_type): username 
            for username in CHESS_PLAYERS.keys()
        }
        
        for future in concurrent.futures.as_completed(future_to_username):
            username = future_to_username[future]
            try:
                data = future.result()
                if data:
                    players_data.append(data)
            except Exception as e:
                print(f"Error processing {username}: {e}")
    
    # Sort players by rating (highest first)
    players_data.sort(key=lambda x: x['rating'] if isinstance(x['rating'], int) else 0, reverse=True)
    
    return players_data

def get_player_format_data(username, format_type):
    """Fetch player data for a specific format"""
    try:
        # Get player profile
        profile_url = f"https://api.chess.com/pub/player/{username}"
        profile_response = requests.get(profile_url, headers=headers, timeout=10)
        
        if profile_response.status_code != 200:
            return None
            
        profile_data = profile_response.json()
        
        # Get player stats
        stats_url = f"https://api.chess.com/pub/player/{username}/stats"
        stats_response = requests.get(stats_url, headers=headers, timeout=10)
        
        if stats_response.status_code != 200:
            return None
            
        stats_data = stats_response.json()
        
        # Extract rating for specific format
        rating = None
        if format_type in stats_data:
            rating = stats_data[format_type].get('last', {}).get('rating', 'N/A')
        
        # Get profile picture
        avatar = profile_data.get('avatar', 'https://www.chess.com/bundles/web/images/user-image.svg')
        
        # Use predefined real name if available, otherwise use API name
        display_name = CHESS_PLAYERS.get(username, profile_data.get('name', username))
        
        return {
            'username': username,
            'display_name': display_name,
            'rating': rating or 'N/A',
            'avatar': avatar,
            'country': profile_data.get('country', '').replace('https://api.chess.com/pub/country/', '').upper(),
            'title': profile_data.get('title', ''),
            'followers': profile_data.get('followers', 0)
        }
        
    except Exception as e:
        print(f"Error fetching {format_type} data for {username}: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)