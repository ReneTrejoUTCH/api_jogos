import requests
from flask import Flask, jsonify, render_template, request
from API_KEY import RAWG_API_KEY, YT_API, CHEAPSHARK_API_URL

app = Flask(__name__)

@app.route("/",methods=['GET'])
def pag_inicial():
    return render_template("index.html")

def get_game_data(game_name):
    url = f"https://api.rawg.io/api/games?key={RAWG_API_KEY}&search={game_name}"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()
    if not data["results"]:
        return None

    game = data["results"][0]  # Tomamos el primer resultado
    return {
        "id": game["id"],
        "name": game["name"],
        "description": game.get("description_raw", "Sin descripción"),
        "image": game["background_image"],
        "released": game.get("released", "Desconocido"),
        "platforms": [p["platform"]["name"] for p in game["platforms"]]
    }

# 🔹 Obtener precio desde CheapShark
def get_game_price(game_name):
    params = {"title": game_name, "pageSize": 10}  # Buscar más resultados
    response = requests.get(CHEAPSHARK_API_URL, params=params)

    if response.status_code != 200:
        return None

    data = response.json()
    if not data:
        return None

    deals = []
    for deal in data:
        deals.append({
            "title": deal["title"],
            "storeID": deal["storeID"],
            "normalPrice": deal["normalPrice"],
            "salePrice": deal["salePrice"],
            "dealRating": deal["dealRating"],
            "dealLink": f"https://www.cheapshark.com/redirect?dealID={deal['dealID']}"
        })

    return deals 

# 🔹 Obtener trailer desde YouTube
def get_youtube_trailer(game_name):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": f"{game_name} official game trailer",
        "key": YT_API,
        "maxResults": 1,
        "type": "video"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None

    data = response.json()
    if not data.get("items"):
        return None

    video = data["items"][0]
    video_id = video["id"]["videoId"]

    return {
        "title": video["snippet"]["title"],
        "video_url": f"https://www.youtube.com/watch?v={video_id}",
        "embed_url": f"https://www.youtube.com/embed/{video_id}"
    }

# 🔹 Endpoint principal para obtener todo
@app.route('/search_game', methods=['GET'])
def search_game():
    game_name = request.args.get("name")

    if not game_name:
        return jsonify({"error": "Debes proporcionar un nombre de juego"}), 400

    game_data = get_game_data(game_name)
    if not game_data:
        return jsonify({"error": "Juego no encontrado en RAWG"}), 404

    game_price = get_game_price(game_name)
    game_trailer = get_youtube_trailer(game_name)

    return jsonify({
        "game": game_data,
        "price": game_price,
        "trailer": game_trailer
    })

if __name__ == '__main__':
    app.run(debug=True)