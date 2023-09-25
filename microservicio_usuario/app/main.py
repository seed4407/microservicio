from enum import Enum

import logging
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId

from fastapi import FastAPI, Query
from pydantic import BaseModel


app = FastAPI()
mongodb_client = MongoClient("demo_01_service_02_mongodb", 27017)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')


class Player(BaseModel):
    id: str | None = None
    name: str
    age: int
    number: int
    team_id: str | None = None
    description: str = ""


class Country(str, Enum):
    chile = 'Chile'
    portugal = 'Portugal'
    españa = 'España'
    francia = "Francia"


class Team(BaseModel):
    id: str | None = None
    name: str
    country: Country

    description: str = ""

    def __init__(self, **kargs):
        if "_id" in kargs:
            kargs["id"] = str(kargs["_id"])
        BaseModel.__init__(self, **kargs)


@app.get("/")
async def root():
    data = [{"id": "1","usuario": "seed4407","tiempo_conectado": 30},{"id": "2","usuario":   "gato_1234","tiempo_conectado": 30},{"id": "3","usuario": "gato_123","tiempo_conectado": 30}]
    return data


def get_players_of_a_team(team_id) -> list[Player]:
        url = f"http://demo_01_service_01:80/players?team_id={team_id}"
        logging.info(f"🌍 Request [GET] {url}")

        return requests.get(url).json()

