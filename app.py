from flask import Flask, request, jsonify, render_template
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno (API keys)
load_dotenv()

app = Flask(__name__)

# Cargar claves de API desde variables de entorno
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_ACCESS_TOKEN = os.getenv("TWITCH_ACCESS_TOKEN")
RAWG_API_KEY = os.getenv("RAWG_API_KEY")
CHEAPSHARK_API_URL = "https://www.cheapshark.com/api/1.0/deals"

# Ruta principal que renderiza index.html
@app.route("/")
def home():
    return render_template("index.html")

# Obtener información del juego desde RAWG
@app.route("/gameinfo")
def get_game_info():
    # Obtener el parámetro 'query' de la solicitud
    query = request.args.get("query")
    if not query:
        # Retorna un error si falta el parámetro
        return jsonify({"error": "Falta el parámetro de búsqueda"}), 400

    # Construir la URL para consultar la API de RAWG
    url = f"https://api.rawg.io/api/games?search={query}&key={RAWG_API_KEY}"
    # Realizar la solicitud a la API
    response = requests.get(url)
    
    # Validar respuesta de la API
    if response.status_code != 200:
        return jsonify({"error": "No se pudo obtener información del juego"}), 500

    # Extraer datos de la respuesta JSON
    data = response.json().get("results", [])
    # Si no se encuentran resultados,
    if not data:
        # Retorna un error.
        return jsonify({"error": "Juego no encontrado"}), 404

    # Tomamos el primer resultado como el juego exacto
    game = data[0]
    # Retornar información relevante del juego
    return jsonify({
        "name": game.get("name", "Desconocido"),
        "description": game.get("description_raw", "Sin descripción"),
        "image": game.get("background_image", ""),
        "release_date": game.get("released", "No disponible"),
        "rating": game.get("rating", "No disponible"),
        "platforms": [p["platform"]["name"] for p in game.get("platforms", [])]
    })

# Buscar precios de juegos relacionados en CheapShark usando el nombre exacto del juego
@app.route("/search_game")
# Definir la función para buscar precios de juegos
def search_game():
    # Obtener el nombre del juego de los parámetros de la solicitud
    game_name = request.args.get("name")
    # Validar que se haya proporcionado un nombre de juego
    # Si no se proporciona, retorna un error
    if not game_name:
        return jsonify({"error": "Debes proporcionar un nombre de juego"}), 400

    # Parámetros para la consulta a CheapShark
    # Se busca el juego por su título y se limita a 10 resultados
    params = {"title": game_name, "pageSize": 10}
    # Realizar la solicitud a la API de CheapShark
    # La URL de la API es una constante definida al inicio del archivo
    # Se pasan los parámetros en la solicitud GET
    response = requests.get(CHEAPSHARK_API_URL, params=params)

    # Validar la respuesta de la API
    # Si la respuesta no es exitosa (código diferente a 200), retorna un error
    if response.status_code != 200:
        return jsonify({"error": "Error al obtener precios"}), 500

    # Extraer los datos de la respuesta JSON
    # La respuesta contiene una lista de ofertas de juegos
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

# Buscar tráiler o gameplay en YouTube para el juego exacto
@app.route("/youtube")
# Definir la función para buscar videos de YouTube
def get_youtube_videos():
    # Obtener el parámetro 'query'
    query = request.args.get("query")
    # Validar que se haya proporcionado un término de búsqueda
    # Si no se proporciona, 
    if not query:
        # retorna un error
        return jsonify({"error": "Falta el parámetro de búsqueda"}), 400

    # Construir la URL y parámetros para la búsqueda en YouTube
    url = "https://www.googleapis.com/youtube/v3/search"
    # Se busca el tráiler o gameplay del juego
    params = {
        # "part" indica qué parte de la respuesta queremos
        # "snippet" incluye información básica como título y descripción
        "part": "snippet",
        # "q" es el término de búsqueda
        # Se busca el juego junto con "trailer" y "gameplay" para obtener resultados relevantes
        "q": f"{query} trailer gameplay",
        "key": YOUTUBE_API_KEY,
        # "maxResults" limita el número de resultados a 6
        "maxResults": 6,
        "type": "video"
    }

    # Realizar la solicitud a la API de YouTube
    # Se pasan los parámetros en la solicitud GET
    response = requests.get(url, params=params)
    # Si la respuesta no es exitosa (código diferente a 200), retorna un error
    if response.status_code != 200:
        return jsonify({"error": "Error al obtener videos"}), 500

    # Extraer los datos de la respuesta JSON
    # La respuesta contiene una lista de videos encontrados
    data = response.json()
    # Validar que se hayan encontrado videos
    # Si no se encuentran, retorna un error
    if "items" not in data or not data["items"]:
        return jsonify({"error": "No se encontraron videos"}), 404

    # Mapear cada video a un objeto con la información necesaria
    videos = [{
        # title es el título del video
        # snippet incluye información básica como título y descripción
        "title": item["snippet"]["title"],
        "videoId": item["id"]["videoId"],
        # embed_url es la URL para embeber el video en un iframe
        # embeber significa que se puede reproducir directamente en la página web
        # Se utiliza el ID del video para construir la URL de embeber
        # La URL de embeber es una forma de mostrar el video sin salir de la aplicación
        "embed_url": f"https://www.youtube.com/embed/{item['id']['videoId']}"
    # Lo que se hace aquí es crear una lista de diccionarios
    # Cada diccionario contiene la información de un video
    } for item in data["items"]]

    # Retornar la lista de videos encontrados
    return jsonify({"videos": videos})

# Buscar streams en vivo en Twitch para el juego exacto
@app.route("/twitch")
# Definir la función para buscar streams en Twitch
def get_twitch_streams():
    # Obtener el nombre del juego de la solicitud
    game_name = request.args.get("game")
    # Validar que se haya proporcionado un nombre de juego
    # Si no se proporciona, retorna un error
    if not game_name:
        return jsonify({"error": "Falta el nombre del juego"}), 400

    # Configurar las cabeceras para la API de Twitch
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {TWITCH_ACCESS_TOKEN}"
    }

    # Obtener el ID del juego en Twitch
    game_url = f"https://api.twitch.tv/helix/games?name={game_name}"
    # Realizar la solicitud a la API de Twitch
    # Se pasan las cabeceras en la solicitud GET
    response = requests.get(game_url, headers=headers)
    # Validar la respuesta de la API
    game_response = response.json()
    # Si la respuesta no contiene datos o no se encuentra el juego, retorna un error
    if "data" not in game_response or not game_response["data"]:
        return jsonify({"error": f"Juego no encontrado en Twitch: {game_name}"}), 404

    # Obtener el ID del juego
    game_id = game_response["data"][0]["id"]

    # Consultar los streams en vivo para el juego
    # Se busca el ID del juego en Twitch
    # Se limita a 5 resultados
    stream_url = f"https://api.twitch.tv/helix/streams?game_id={game_id}&first=5"
    # Realizar la solicitud a la API de Twitch
    # Se pasan las cabeceras en la solicitud GET
    stream_response = requests.get(stream_url, headers=headers).json()
    # Validar la respuesta de la API
    # Si la respuesta no contiene datos o no se encuentran streams, retorna un error
    if "data" not in stream_response or not stream_response["data"]:
        return jsonify({"error": "No se encontraron streams en vivo"}), 404

    # Mapear la información de cada stream
    # Cada stream se convierte en un diccionario con la información relevante
    # Se utiliza una lista por comprensión para crear la lista de streams
    streams = [{
        "user_name": stream["user_name"],
        "viewer_count": stream["viewer_count"],
        "title": stream["title"],
        # thumbnail_url es la URL de la miniatura del stream
        # Se reemplazan los placeholders {width} y {height} por valores específicos 
        "thumbnail_url": stream["thumbnail_url"].replace("{width}", "300").replace("{height}", "200"), 
    } for stream in stream_response["data"]]
    # Retornar la lista de streams encontrados
    return jsonify({"data": streams})

# Iniciar la aplicación en modo debug
if __name__ == "__main__":
    app.run(debug=True)
