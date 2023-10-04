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

    model_config = {
        "json_schema_extra": {
            "ejemplo cantidad": [
                {
                    "cantidad": 1,
                }
            ]
        }
    }


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

# @app.on_event("startup")
@app.get("/",response_model =  str,response_description="Inicia proceso de envio de anuncios",summary = "Iniciar microservicio", tags=["Inicio"])
async def root(background_tasks: BackgroundTasks, interval = 1):
    background_tasks.add_task(comunicacion_publicidad, background_tasks, interval)
    logging.info("👋")
    return {"message": "Tarea periódica iniciada"}

@app.post("/anuncio",response_model=str,response_description="Creacion exitosa",summary = "Creacion anuncio", tags=["anuncio"])
def creacion_anuncio(anuncio: publicidad):
    """
    Agregar anuncio a base de datos, con los siguientes parametros:

    - **name**: titulo para identificar a quien pertenece el anuncio, string
    - **description**: contenido del anuncio, string
    """
    try:
        global id_anuncios
        anuncio.id = str(id_anuncios)
        id_anuncios = id_anuncios + 1
        inserted_id = mongodb_client.service_01.anuncios.insert_one(
            anuncio.dict()
        ).inserted_id
        return "Ok"
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=504, detail="Tiempo limite alcanzado")
    except pymongo.errors.ConnectionFailure:
        raise HTTPException(status_code=503, detail="No se pudo concectar a la base de datos")

@app.put("/cantidad",response_model=str,response_description="Actualizacion exitosa",summary = "Reiniciar id anuncios", tags=["cantidad"])
def actualizar_id():
    """
    Actualizar valor almacenado en base de datos cantidades a 1

    **sin parametros de entrada**
    """
    try:
        if(mongodb_client.service_01.cantidades.find_one() == None):
            raise HTTPException(status_code=404, detail="No se encontro valor para actualizar")
        else:
            global id_anuncios
            id_anuncios = 1
            mongodb_client.service_01.cantidades.update_one({},{"$set": {"cantidad":1}})
            return "Ok"
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=504, detail="Tiempo limite alcanzado")
    except pymongo.errors.ConnectionFailure:
        raise HTTPException(status_code=503, detail="No se pudo concectar a la base de datos")


@app.get("/anuncio/{anuncio_id}",response_model=publicidad,response_description="Obtencion exitosa",summary = "Obtencion anuncio", tags=["anuncio"])
def anuncio_get(anuncio_id: str):
    """
    Obtencion anuncio con id == anuncio_id, recibe el parametro:
    
    - **anuncio_id**: id anunico a buscar, str
    """
    try:
        dato = mongodb_client.service_01.anuncios.find_one({"id": anuncio_id})
        if(dato == None):
            raise HTTPException(status_code=404, detail="No se encontro anuncio")
        else:
            return publicidad(**dato)
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=504, detail="Tiempo limite alcanzado")
    except pymongo.errors.ConnectionFailure:
        raise HTTPException(status_code=503, detail="No se pudo concectar a la base de datos")
    

@app.get("/anuncio_all",response_model=list[publicidad],response_description="Obtencion exitosa",summary = "Obtencion todos los anuncio", tags=["anuncio"])
def anuncio_all():
    """
    Obtencion de todos los anuncios
    
    **sin parametros de entrada**
    """
    try:
        if(mongodb_client.service_01.anuncios.find_one() == None):
            raise HTTPException(status_code=404, detail="No se encontro anuncio")
        else:
            return [publicidad(**anuncio) for anuncio in mongodb_client.service_01.anuncios.find()]
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=504, detail="Tiempo limite alcanzado")
    except pymongo.errors.ConnectionFailure:
        raise HTTPException(status_code=503, detail="No se pudo concectar a la base de datos")


@app.get("/cantidad_all",response_model=list[cantidad],response_description="Obtencion exitosa",summary = "Obtencion ultimo id anuncio+1", tags=["cantidad"])
def cantidad_all():
    """
    Obtencion de id anuncio siguiente al ultimo agregado
    
    **sin parametros de entrada**
    """
    try:
        if(mongodb_client.service_01.cantidades.find_one() == None):
            raise HTTPException(status_code=404, detail="No se encontro ningun valor en cantidad")
        else:
            return [cantidad(**dato) for dato in mongodb_client.service_01.cantidades.find()]
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=504, detail="Tiempo limite alcanzado")
    except pymongo.errors.ConnectionFailure:
        raise HTTPException(status_code=503, detail="No se pudo concectar a la base de datos")

@app.delete("/anuncios_eliminar/{anuncio_id}",response_model=str,response_description="Eliminacion exitosa",summary = "Eliminar anuncio", tags=["anuncio"])
def anuncios_eliminar(anuncio_id: str):
    """
    Eliminacion anuncio con id == anuncio_id, recibe el parametro:
    
    - **anuncio_id**: id anuncio a eliminar, string
    """
    try:
        if(mongodb_client.service_01.anuncios.find_one({"id": anuncio_id}) == None):
            raise HTTPException(status_code=404, detail="No se encontro ningun anuncio con dicho id")
        else:
            result = mongodb_client.service_01.anuncios.delete_one(
                {"id": anuncio_id}
            )
            return "Ok"
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=504, detail="Tiempo limite alcanzado")
    except pymongo.errors.ConnectionFailure:
        raise HTTPException(status_code=503, detail="No se pudo concectar a la base de datos")

@app.on_event("shutdown")
async def fin_proceso():
    try:
        global id_anuncios
        mongodb_client.service_01.cantidades.update_one({},{"$set": {"cantidad":id_anuncios}})
    except pymongo.errors.ServerSelectionTimeoutError:
        raise HTTPException(status_code=504, detail="Tiempo limite alcanzado")
    except pymongo.errors.ConnectionFailure:
        raise HTTPException(status_code=503, detail="No se pudo concectar a la base de datos")
