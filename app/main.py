import logging

from pymongo import MongoClient
from bson.objectid import ObjectId
from fastapi import FastAPI
from fastapi import BackgroundTasks
# from fastapi import Body
from fastapi import HTTPException
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
            raise HTTPException(status_code=503, detail="No se pudo conectar a servidor")
        
        except requests.exceptions.HTTPError as e:
            raise HTTPException(status_code=404, detail="No se encontro recurso")

        except requests.exceptions.Timeout as e:
            raise HTTPException(status_code=504, detail="Tiempo limite para respuesta alcanzado")

        estado = data[0]["estado"]
        if(estado == "conectado"):
            anuncios_para_enviar = mongodb_client.service_01.anuncios.find_one({ "id": { "$gte": str(contador_anuncios) } })
            if(anuncios_para_enviar == None):
                contador_anuncios = 0
                anuncios_para_enviar = mongodb_client.service_01.anuncios.find_one({ "id": { "$gte": str(contador_anuncios) } })
                contador_anuncios = int(anuncios_para_enviar["id"]) + 1
            else:
                contador_anuncios = int(anuncios_para_enviar["id"]) + 1
            try: 
                connection = pika.BlockingConnection(pika.ConnectionParameters(host='172.18.0.6'))
            except pika.exceptions.AMQPConnectionError as e:
                raise HTTPException(status_code=503, detail="No se pudo conectar a la cola rabbitMQ")

            channel = connection.channel()
            # channel.queue_declare(queue='hello')
            channel.basic_publish(exchange='', routing_key='publicidad', body=anuncios_para_enviar["description"])
            connection.close()
        time.sleep(interval)

class publicidad(BaseModel):
    id: str | None = None
    name: str
    description: str

    model_config = {
        "json_schema_extra": {
            "ejemplo publicidad": [
                {
                    "name": "Melt Pizza",
                    "description": "2x1 en todas las pizzas familiares",
                }
            ]
        }
    }

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

@app.get("/",response_description="Inicia proceso de envio de anuncios", tags=["Inicio"])
async def root(background_tasks: BackgroundTasks, interval = 1):
    background_tasks.add_task(comunicacion_publicidad, background_tasks, interval)
    logging.info("👋")
    return {"message": "Tarea periódica iniciada"}

@app.post("/anuncio",response_description="Creacion anuncio", tags=["anuncio"])
def creacion_anuncio(anuncio: publicidad):
    """
    Datos anuncio para agregar a base de datos:

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

@app.put("/cantidad",response_description="Actualizacion dato id anuncios a 1", tags=["cantidad"])
def actualizar_id():
    global id_anuncios
    id_anuncios = 1
    mongodb_client.service_01.cantidades.update_one({},{"$set": {"cantidad":1}})

@app.get("/anuncio/{anuncio_id}", response_description="Obtencion anuncio con id == anuncio_id", tags=["anuncio"])
def anuncio_get(anuncio_id: str):
    dato = mongodb_client.service_01.anuncios.find_one({"id": anuncio_id})
    if(dato == None):
        raise HTTPException(status_code=404, detail="No se encontro anuncio")
    else:
        return publicidad(**dato)

@app.get("/anuncio_all",response_description="Obtencion de todos los anuncios", tags=["anuncio"])
def anuncio_all():
    if(mongodb_client.service_01.anuncios.find_one() == None):
        raise HTTPException(status_code=404, detail="No se encontro anuncio")
    else:
        return [publicidad(**anuncio) for anuncio in mongodb_client.service_01.anuncios.find()]

@app.get("/cantidad_all",response_description="Obtencion de id anuncio siguiente al ultimo agregado", tags=["cantidad"])
def anuncio_all():
    if(mongodb_client.service_01.cantidades.find_one() == None):
        raise HTTPException(status_code=404, detail="No se encontro ningun valor en cantidad")
    else:
        return [cantidad(**dato) for dato in mongodb_client.service_01.cantidades.find()]

@app.delete("/anuncios_eliminar/{anuncio_id}",response_description="Elimina anuncio con id == anuncio_id", tags=["anuncio"])
def anuncios_eliminar(anuncio_id: str):
    result = mongodb_client.service_01.anuncios.delete_one(
        {"id": anuncio_id}
    )
    return result.deleted_count

@app.on_event("shutdown")
async def fin_proceso():
    global id_anuncios
    mongodb_client.service_01.cantidades.update_one({},{"$set": {"cantidad":id_anuncios}})
