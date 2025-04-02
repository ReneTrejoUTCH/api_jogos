from flask import Flask, request, jsonify, render_template
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 🔹 Cargar claves de API desde variables de entorno
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
RAWG_API_KEY = os.getenv("RAWG_API_KEY")
CHEAPSHARK_API_URL = "https://www.cheapshark.com/api/1.0/deals"

@app.route("/")
def home():
    return render_template("index.html")

# 🔹 Obtener información del juego desde RAWG
@app.route("/gameinfo")
def get_game_info():
    query = request.args.get("query")
    url = f"https://api.rawg.io/api/games?search={query}&key={RAWG_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json().get("results", [])
        if not data:
            return jsonify({"error": "Juego no encontrado"}), 404

        game = data[0]  # Tomar el primer resultado
        return jsonify({
            "name": game.get("name", "Desconocido"),
            "description": game.get("description_raw", "Sin descripción"),
            "image": game.get("background_image", ""),
            "release_date": game.get("released", "No disponible"),
            "rating": game.get("rating", "No disponible"),
            "platforms": [p["platform"]["name"] for p in game.get("platforms", [])]
        })
    return jsonify({"error": "No se pudo obtener información del juego"}), 500

# 🔹 Obtener precios desde CheapShark
@app.route("/search_game")
def search_game():
    game_name = request.args.get("name")
    if not game_name:
        return jsonify({"error": "Debes proporcionar un nombre de juego"}), 400
    
    params = {"title": game_name, "pageSize": 10}
    response = requests.get(CHEAPSHARK_API_URL, params=params)
    
    if response.status_code != 200:
        return jsonify({"error": "Error al obtener precios"}), 500
    
    data = response.json()
    deals = [{
        "title": deal["title"],
        "normalPrice": deal["normalPrice"],
        "salePrice": deal["salePrice"],
        "dealLink": f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"
    } for deal in data]
    
    return jsonify({"price": deals})

# # 🔹 Obtener tráiler desde YouTube
@app.route("/youtube")
def get_youtube_videos():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Falta el parámetro de búsqueda"}), 400

    url = f"https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} trailer",
        "key": YOUTUBE_API_KEY,
        "maxResults": 6,
        "type": "video"
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" not in data or not data["items"]:
        return jsonify({"error": "No se encontraron videos"}), 404

    videos = [
        {
            "title": item["snippet"]["title"],
            "videoId": item["id"]["videoId"],
            "embed_url": f"https://www.youtube.com/embed/{item['id']['videoId']}"
        }
        for item in data["items"]
    ]

    return jsonify({"videos": videos})

# 🔹 Obtener streams de Twitch

@app.route("/twitch")
def get_twitch_streams():
    game_name = request.args.get("game")
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
    }
    
    game_url = f"https://api.twitch.tv/helix/games?name={game_name}"
    response = requests.get(game_url, headers=headers)
    game_response = response.json()

    print("🔍 Respuesta de Twitch para el juego:", game_response)  # Debugging

    if "data" not in game_response or not game_response["data"]:
        return jsonify({"error": f"Juego no encontrado en Twitch: {game_name}"}), 404

    game_id = game_response["data"][0]["id"]

    stream_url = f"https://api.twitch.tv/helix/streams?game_id={game_id}&first=5"
    stream_response = requests.get(stream_url, headers=headers).json()

    print("📺 Respuesta de Twitch Streams:", stream_response)  # Debugging

    if "data" not in stream_response or not stream_response["data"]:
        return jsonify({"error": "No se encontraron streams en vivo"}), 404
    
    streams = [{
    "user_name": stream["user_name"],
    "viewer_count": stream["viewer_count"],
    "title": stream["title"],
    "thumbnail_url": stream["thumbnail_url"].replace("{width}", "300").replace("{height}", "200"),
    "embed_url": f"https://player.twitch.tv/?channel={stream['user_name']}&parent=localhost&parent=127.0.0.1"
    } for stream in stream_response["data"]]


    return jsonify({"data": streams})

if __name__ == "__main__":
    app.run(debug=True)