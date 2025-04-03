# app.py: API backend de LootBox
from flask import Flask, request, jsonify, render_template
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno (API keys, etc.)
load_dotenv()

app = Flask(__name__)

# 🔹 Cargar claves de API desde variables de entorno
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
RAWG_API_KEY = os.getenv("RAWG_API_KEY")
CHEAPSHARK_API_URL = "https://www.cheapshark.com/api/1.0/deals"

# Ruta principal que renderiza index.html
@app.route("/")
def home():
    return render_template("index.html")

# 🔹 Obtener información del juego desde RAWG
@app.route("/gameinfo")
def get_game_info():
    # Obtener el parámetro 'query' de la solicitud
    query = request.args.get("query")
    if not query:
        # Retornar error si falta el parámetro
        return jsonify({"error": "Falta el parámetro de búsqueda"}), 400

    # Construir la URL para consultar la API de RAWG
    url = f"https://api.rawg.io/api/games?search={query}&key={RAWG_API_KEY}"
    response = requests.get(url)
    
    # Validar respuesta de la API
    if response.status_code != 200:
        return jsonify({"error": "No se pudo obtener información del juego"}), 500

    data = response.json().get("results", [])
    if not data:
        # Retornar error si no se encuentra el juego
        return jsonify({"error": "Juego no encontrado"}), 404

    # Tomamos el primer resultado como el juego exacto buscado
    game = data[0]
    return jsonify({
        "name": game.get("name", "Desconocido"),
        "description": game.get("description_raw", "Sin descripción"),
        "image": game.get("background_image", ""),
        "release_date": game.get("released", "No disponible"),
        "rating": game.get("rating", "No disponible"),
        "platforms": [p["platform"]["name"] for p in game.get("platforms", [])]
    })

# 🔹 Buscar precios en CheapShark usando el nombre exacto del juego
@app.route("/search_game")
def search_game():
    # Obtener el nombre del juego de los parámetros de la solicitud
    game_name = request.args.get("name")
    if not game_name:
        return jsonify({"error": "Debes proporcionar un nombre de juego"}), 400

    # Parámetros para la consulta a CheapShark
    params = {"title": game_name, "pageSize": 10}
    response = requests.get(CHEAPSHARK_API_URL, params=params)

    if response.status_code != 200:
        return jsonify({"error": "Error al obtener precios"}), 500

    data = response.json()
    # Mapear cada oferta a un objeto con la información relevante
    deals = [{
        "title": deal["title"],
        "normalPrice": deal["normalPrice"],
        "salePrice": deal["salePrice"],
        "dealLink": f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"
    } for deal in data]

    # Retornar la lista de ofertas (vacía si no se encontraron)
    return jsonify({"price": deals})

# 🔹 Buscar tráiler en YouTube para el juego exacto
@app.route("/youtube")
def get_youtube_videos():
    # Obtener el parámetro 'query'
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Falta el parámetro de búsqueda"}), 400

    # Construir la URL y parámetros para la búsqueda en YouTube
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{query} trailer gameplay",
        "key": YOUTUBE_API_KEY,
        "maxResults": 6,
        "type": "video"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return jsonify({"error": "Error al obtener videos"}), 500

    data = response.json()
    if "items" not in data or not data["items"]:
        return jsonify({"error": "No se encontraron videos"}), 404

    # Mapear cada video a un objeto con la información necesaria
    videos = [{
        "title": item["snippet"]["title"],
        "videoId": item["id"]["videoId"],
        "embed_url": f"https://www.youtube.com/embed/{item['id']['videoId']}"
    } for item in data["items"]]

    return jsonify({"videos": videos})

# 🔹 Buscar streams en vivo en Twitch para el juego exacto
@app.route("/twitch")
def get_twitch_streams():
    # Obtener el nombre del juego de la solicitud
    game_name = request.args.get("game")
    if not game_name:
        return jsonify({"error": "Falta el nombre del juego"}), 400

    # Configurar las cabeceras para la API de Twitch
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
    }

    # Obtener el ID del juego en Twitch
    game_url = f"https://api.twitch.tv/helix/games?name={game_name}"
    response = requests.get(game_url, headers=headers)
    game_response = response.json()

    if "data" not in game_response or not game_response["data"]:
        return jsonify({"error": f"Juego no encontrado en Twitch: {game_name}"}), 404

    game_id = game_response["data"][0]["id"]

    # Consultar los streams en vivo para el juego
    stream_url = f"https://api.twitch.tv/helix/streams?game_id={game_id}&first=5"
    stream_response = requests.get(stream_url, headers=headers).json()

    if "data" not in stream_response or not stream_response["data"]:
        return jsonify({"error": "No se encontraron streams en vivo"}), 404

    # Mapear la información de cada stream
    streams = [{
        "user_name": stream["user_name"],
        "viewer_count": stream["viewer_count"],
        "title": stream["title"],
        "thumbnail_url": stream["thumbnail_url"].replace("{width}", "300").replace("{height}", "200"),
        "embed_url": f"https://player.twitch.tv/?channel={stream['user_name']}&parent=localhost&parent=127.0.0.1"
    } for stream in stream_response["data"]]

    return jsonify({"data": streams})

# Iniciar la aplicación en modo debug
if __name__ == "__main__":
    app.run(debug=True)
