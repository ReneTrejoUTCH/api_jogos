from flask import Flask, render_template, request, jsonify
import requests # type: ignore
app = Flask(__name__)

API_KEY = "d401df7ed0e24f59891347be0d003fd5"
JUEGO = "the-last-of-us"

url = f"https://api.rawg.io/api/games/{JUEGO}?key={API_KEY}"

response = requests.get(url)

@app.route("/")
def inicio():
    return render_template("index.html")

if response.status_code == 200:
    data = response.json()

    print(f"Nombre: {data['name']}")
    print(f"Fecha de lanzamiento: {data['released']}")
    print(f"Rating: {data['rating']} / 5")
    print(f"Disponible en: ")

    for store in data.get("stores",[]):
        store_name = store["store"]["name"]
        store_url = store["store"]["domain"]
        print(f" - {store_name}: {store_url}")
else:
    print("Error al obtener los datos del juego")
