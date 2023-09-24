import logging

from pymongo import MongoClient
from bson.objectid import ObjectId
from fastapi import FastAPI
from fastapi import BackgroundTasks
from pydantic import BaseModel
import requests

def comunicacion_publicidad(background_tasks: BackgroundTasks):
    try:
        response = requests.get('http://microservicio_destino:puerto/ruta_del_endpoint')
        response.raise_for_status()  # Verificar el código de estado HTTP
        # Procesar la respuesta exitosa
        data = response.json()
        print(data)
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Tiempo de espera agotado: {e}")



app = FastAPI()
mongodb_client = MongoClient("demo_01_service_01_mongodb", 27017)

logging.basicConfig(level = logging.DEBUG,
                    format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s')

class publicidad(BaseModel):
    id: str
    name: str
    description: str

    def __init__(self, **kargs):
        if "_id" in kargs:
            kargs["id"] = str(kargs["_id"])
        BaseModel.__init__(self, **kargs)

@app.get("/")
async def root(background_tasks: BackgroundTasks):
    background_tasks.add_task(comunicacion_publicidad, background_tasks)
    logging.info("👋 Hello world (end-point)!")
    return {"message": "Tarea periódica iniciada"}


@app.get("/players")
def players_all(team_id: str | None = None):
    filters = {}

    if team_id:
        filters["team_id"] = team_id

    return [Player(**player) for player in mongodb_client.service_01.players.find(filters)]

@app.get("/players/{player_id}")
def players_get(player_id: str):
    return Player(**mongodb_client.service_01.players.find_one({"_id": ObjectId(player_id)}))

@app.delete("/players/{player_id}")
def players_delete(player_id: str):
    mongodb_client.service_01.players.delete_one(
        {"_id": ObjectId(player_id)}
    )
    return "ok"

@app.post("/players")
def players_create(player: Player):
    inserted_id = mongodb_client.service_01.players.insert_one(
        player.dict()
    ).inserted_id

    new_player = Player(
        **mongodb_client.service_01.players.find_one(
            {"_id": ObjectId(inserted_id)}
        )
    )

    logging.info(f"✨ New player created: {new_player}")

    return new_player