import logging

from pymongo import MongoClient
from bson.objectid import ObjectId
from fastapi import FastAPI
from fastapi import BackgroundTasks
from pydantic import BaseModel
import requests
import time
importar pika

def comunicacion_publicidad(background_tasks, interval):
    while True:
        try:
            response = requests.get('http://172.18.0.3:80/')
            response.raise_for_status()  # Verificar el código de estado HTTP
            # Procesar la respuesta exitosa
            data = response.json()
            for usuario in data:
                id_usuario = usuario["id"]
                nombre_usuario = usuario["usuario"]
                tiempo_conectado = usuario["tiempo_conectado"]
                logging.info(nombre_usuario)
        except requests.exceptions.RequestException as e:
            logging.info(f"Error de conexión: {e}")
        except requests.exceptions.HTTPError as e:
            logging.info(f"Error HTTP: {e}")
        except requests.exceptions.Timeout as e:
            logging.info(f"Tiempo de espera agotado: {e}")
        
        # conexión = pika.BlockingConnection(pika.ConnectionParameters(host= 'localhost' ))
        # canal = conexión.canal()    
        # canal.queue_declare(cola= 'hola' )
        # canal.basic_publish(exchange= '' , route_key= 'hola' , body= '¡Hola mundo!' )
        print ( " [x] Enviado '¡Hola mundo!'" )
        time.sleep(interval)

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
async def root(background_tasks: BackgroundTasks, interval = 5):
    background_tasks.add_task(comunicacion_publicidad, background_tasks, interval)
    logging.info("👋")
    return {"message": "Tarea periódica iniciada"}


