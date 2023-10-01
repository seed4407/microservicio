import logging

from pymongo import MongoClient
from bson.objectid import ObjectId
from fastapi import FastAPI
from fastapi import BackgroundTasks
from pydantic import BaseModel
import requests
import time
import pika
import signal

def comunicacion_publicidad(background_tasks, interval):
    contador_anuncios = 0
    while True:
        try:
            response = requests.get('http://172.18.0.5:80/')
            response.raise_for_status()  # Verificar el código de estado HTTP
            # Procesar la respuesta exitosa
            data = response.json()

        except requests.exceptions.RequestException as e:
            logging.info(f"Error de conexión: {e}")
        except requests.exceptions.HTTPError as e:
            logging.info(f"Error HTTP: {e}")
        except requests.exceptions.Timeout as e:
            logging.info(f"Tiempo de espera agotado: {e}")

        estado = data[0]["estado"]
        if(estado == "conectado"):
            anuncios_para_enviar = mongodb_client.service_01.anuncios.find_one({ "id": { "$gte": str(contador_anuncios) } })
            if(anuncios_para_enviar == None):
                contador_anuncios = 0
                anuncios_para_enviar = mongodb_client.service_01.anuncios.find_one({ "id": { "$gte": str(contador_anuncios) } })
                contador_anuncios = int(anuncios_para_enviar["id"]) + 1
            else:
                contador_anuncios = int(anuncios_para_enviar["id"]) + 1
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='172.18.0.6'))
            channel = connection.channel()
            # channel.queue_declare(queue='hello')
            channel.basic_publish(exchange='', routing_key='publicidad', body=anuncios_para_enviar["description"])
            connection.close()
        time.sleep(interval)

class publicidad(BaseModel):
    id: str | None = None
    name: str
    description: str

class cantidad(BaseModel):
    cantidad: int

app = FastAPI()
mongodb_client = MongoClient("demo_01_service_01_mongodb", 27017)

logging.basicConfig(level = logging.DEBUG,
                    format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
                    encoding='utf-8')

dato = mongodb_client.service_01.cantidades.find_one()
if(dato == None):
    valor_inicial = cantidad(cantidad=1)
    resultado = mongodb_client.service_01.cantidades.insert_one(
        valor_inicial.dict()
    )
    id_anuncios = 1
else:
    id_anuncios = int(dato["cantidad"])

@app.get("/")
async def root(background_tasks: BackgroundTasks, interval = 1):
    background_tasks.add_task(comunicacion_publicidad, background_tasks, interval)
    logging.info("👋")
    return {"message": "Tarea periódica iniciada"}

@app.post("/anuncio",response_description="Anuncio creado")
def creacion_anuncio(anuncio: publicidad):
    """
    Datos anuncio que se creara de anuncion que se enviaran:

    - **name**: titulo para identificar a quien pertenece el anuncio
    - **description**: contenido del anuncio
    """
    global id_anuncios
    anuncio.id = str(id_anuncios)
    id_anuncios = id_anuncios + 1
    inserted_id = mongodb_client.service_01.anuncios.insert_one(
        anuncio.dict()
    ).inserted_id

    new_anuncio = publicidad(
        **mongodb_client.service_01.anuncios.find_one(
            {"_id": ObjectId(inserted_id)}
        )
    )

    logging.info(f"✨ New anuncio created: {new_anuncio}")

    return new_anuncio

@app.put("/cantidad")
def actualizar_id():
    global id_anuncios
    id_anuncios = 1
    mongodb_client.service_01.cantidades.update_one({},{"$set": {"cantidad":1}})

@app.get("/anuncio/{anuncio_id}")
def anuncio_get(anuncio_id: str):
    dato = mongodb_client.service_01.anuncios.find_one({"id": anuncio_id})
    if(dato == None):
        return None
    else:
        return publicidad(**dato)

@app.get("/anuncio_all")
def anuncio_all():
    return [publicidad(**anuncio) for anuncio in mongodb_client.service_01.anuncios.find()]

@app.get("/cantidad_all")
def anuncio_all():
    return [cantidad(**dato) for dato in mongodb_client.service_01.cantidades.find()]

@app.delete("/anuncios_eliminar/{anuncio_id}")
def anuncios_eliminar(anuncio_id: str):
    result = mongodb_client.service_01.anuncios.delete_one(
        {"id": anuncio_id}
    )
    return result.deleted_count

@app.on_event("shutdown")
async def fin_proceso():
    global id_anuncios
    mongodb_client.service_01.cantidades.update_one({},{"$set": {"cantidad":id_anuncios}})
