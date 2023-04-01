import os
import re
import requests
import sys
from datetime import timedelta
import datetime
import asyncio
import confluent_kafka
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.protobuf import ProtobufSerializer
from confluent_kafka.serialization import SerializationContext, MessageField
import schema_car_pb2 as schema_car_pb2
import schema_bike_pb2 as schema_bike_pb2


kafka_url = os.getenv("KAFKA_URL", "localhost:9092")
port_schema_host = os.getenv("SCHEMA_HOST", "http://localhost")
port_schema_registry = "8084"
day = 1 #how many days ago do we take the data?

def getBikeRecords(limite=-1):
    yesterday = (datetime.datetime.now() - timedelta(days=day)).strftime(
        "%Y-%m-%d %H:00:00"
    )
    print("call for time: " + yesterday)
    req = (
        "https://opendata.paris.fr/api/v2/catalog/datasets/comptage-velo-donnees-compteurs/exports/json?select=%2A&where=date%20%3D%20date%27"
        + yesterday
        + "%27&limit="
        + str(limite)
        + "&offset=0&timezone=UTC"
    )
    response = requests.get(req)

    if response.status_code == 200:
        print("Success!")
    else:
        print("Not Found.")
    print("number of results", len(response.json()))
    return response.json()


def getCarRecords(limite=-1):
    yesterday = (datetime.datetime.now() - timedelta(days=day)).strftime(
        "%Y-%m-%d %H:00:00"
    )
    print("call for time: " + yesterday)
    req = (
        "https://opendata.paris.fr/api/v2/catalog/datasets/comptages-routiers-permanents/exports/json?select=%2A&where=t_1h%20%3D%20date%27"
        + yesterday
        + "%27&limit="
        + str(limite)
        + "&offset=0&timezone=UTC"
    )
    response = requests.get(req)

    if response.status_code == 200:
        print("Success!")
    else:
        print("Not Found. code: " + str(response.status_code))
        print(response.text)
    print("number of results", len(response.json()))
    return response.json()


def bikeStream(bike_records, background_tasks, kafka_producer):
    schema_registry_client = SchemaRegistryClient({'url': f"{port_schema_host}:{port_schema_registry}"})
    protobuf_serializer_bike = ProtobufSerializer(
        schema_bike_pb2.BikeRecord,
        schema_registry_client,
        {'use.deprecated.format': False}
    )
    for record in bike_records:
        task = asyncio.ensure_future(simulateBikeStream(record, kafka_producer, protobuf_serializer_bike))
        background_tasks.append(task)


def carStream(car_records, background_tasks, kafka_producer):
    schema_registry_client = SchemaRegistryClient({'url': f"{port_schema_host}:{port_schema_registry}"})
    protobuf_serializer_car = ProtobufSerializer(
        schema_car_pb2.CarRecord,
        schema_registry_client,
        {'use.deprecated.format': False}
    )
    for record in car_records:
        task = asyncio.ensure_future(simulateCarStream(record, kafka_producer, protobuf_serializer_car))
        background_tasks.append(task)


async def simulateBikeStream(record, kafka_producer, protobuf_serializer_bike):
    n_total_counter = int(record["sum_counts"])
    nb_seconds = 3600 - datetime.datetime.now().minute * 60 - datetime.datetime.now().second
    percentage_records = nb_seconds / 3600
    n_counter = round(n_total_counter * percentage_records)
    if n_counter > 0:
        for _ in range(n_counter):
            sleep_time = nb_seconds / n_counter
            date = (datetime.datetime.now() - timedelta(days=day)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            bike_record = schema_bike_pb2.BikeRecord(
                id_compteur=record["id_compteur"],
                id=record["id"],
                nom_compteur=record["nom_compteur"],
                date=date,#record["date"],
                name=record["name"],
                lat=record["coordinates"]["lat"],
                lon=record["coordinates"]["lon"]
            )

            kafka_producer.produce(topic="bike",
                    key=record["nom_compteur"],
                    value=protobuf_serializer_bike(bike_record, SerializationContext("bike", MessageField.VALUE))
                    )
            kafka_producer.poll(0)
            await asyncio.sleep(sleep_time)
    return 0


async def simulateCarStream(record, kafka_producer, protobuf_serializer_car):
    if record["q"]:
        n_total_counter = int(record["q"])
        nb_seconds = 3600 - datetime.datetime.now().minute * 60 - datetime.datetime.now().second
        percentage_records = nb_seconds / 3600
        n_counter = round(n_total_counter * percentage_records)
        if n_counter > 0:
            for _ in range(n_counter):
                sleep_time = nb_seconds / n_counter
                date = (datetime.datetime.now() - timedelta(days=day)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                car_record = schema_car_pb2.CarRecord(
                    id_compteur=record["iu_ac"],
                    nom_compteur=record["libelle"],
                    date=date,#record["t_1h"],
                    etat_trafic=record["etat_trafic"],
                    compteur_amont=record["iu_nd_amont"],
                    nom_compteur_amont=record["libelle_nd_amont"],
                    id_compteur_aval=record["iu_nd_aval"],
                    nom_compteur_aval=record["libelle_nd_aval"],
                    lat=record["geo_point_2d"]["lat"] if record["geo_point_2d"] != None else 0, 
                    lon=record["geo_point_2d"]["lon"] if record["geo_point_2d"] != None else 0
                )

                kafka_producer.produce(topic="car",
                        key=record["iu_ac"],
                        value=protobuf_serializer_car(car_record, SerializationContext("car", MessageField.VALUE))
                        )
                kafka_producer.poll(0)
                await asyncio.sleep(sleep_time)
    return 0


async def main():
    bike_records = getBikeRecords()
    car_records = getCarRecords()
    background_tasks = []
    
    kafka_producer = confluent_kafka.Producer(
        {"bootstrap.servers": kafka_url, "client.id": "producer"}
    )
    print("Sending bike records")
    bikeStream(bike_records, background_tasks, kafka_producer)
    print("Sending car records")
    carStream(car_records, background_tasks, kafka_producer)
    res = await asyncio.gather(*background_tasks)
    return res


asyncio.run(main())
