import re
import requests
from datetime import timedelta
import datetime
import asyncio
import confluent_kafka
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.protobuf import ProtobufSerializer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
import json
import schema_pb2 as schema_pb2

port_schema_registry = "8084"

def getBikeRecords(limite=-1):
    yesterday = (datetime.datetime.now() - timedelta(days=2)).strftime(
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
    yesterday = (datetime.datetime.now() - timedelta(days=1)).strftime(
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
    for record in bike_records:
        task = asyncio.ensure_future(simulateBikeStream(record, kafka_producer))
        background_tasks.append(task)


def carStream(car_records, background_tasks, kafka_producer):
    for record in car_records:
        task = asyncio.ensure_future(simulateCarStream(record, kafka_producer))
        background_tasks.append(task)


async def simulateBikeStream(record, kafka_producer):
    string_serializer = StringSerializer('utf8')
    schema_registry_client = SchemaRegistryClient({'url': "http://localhost:"+port_schema_registry})
    protobuf_serializer_bike = ProtobufSerializer(
        schema_pb2.BikeRecord,
        schema_registry_client,
        {'use.deprecated.format': False}
    )
    n_counter = int(record["sum_counts"])
    if n_counter > 0:
        for i in range(n_counter):
            sleep_time = 3500 / n_counter
            coordinates = schema_pb2.Coordinates(
                lat=record["coordinates"]["lat"], 
                lon=record["coordinates"]["lon"]
            )
            bike_record = schema_pb2.BikeRecord(
                id_compteur=record["id_compteur"],
                id=record["id"],
                nom_compteur=record["nom_compteur"],
                date=record["date"],
                name=record["name"],
                coord=coordinates,
            )

            kafka_producer.produce(topic="bike",
                    key=string_serializer("bike","utf-8"),
                    value=protobuf_serializer_bike(bike_record, SerializationContext("bike", MessageField.VALUE))
                    )
            kafka_producer.poll(0)
            await asyncio.sleep(sleep_time)
    return 0


async def simulateCarStream(record, kafka_producer):
    string_serializer = StringSerializer('utf8')
    schema_registry_client = SchemaRegistryClient({'url': "http://localhost:"+port_schema_registry})
    protobuf_serializer_car = ProtobufSerializer(
        schema_pb2.CarRecord,
        schema_registry_client,
        {'use.deprecated.format': False}
    )
    if record["q"]:
        n_counter = int(record["q"])
        if n_counter > 0:
            for i in range(n_counter):
                sleep_time = 3500 / n_counter
                coordinates = schema_pb2.Coordinates(
                    lat=record["geo_point_2d"]["lat"] if record["geo_point_2d"] != None else 0, 
                    lon=record["geo_point_2d"]["lon"] if record["geo_point_2d"] != None else 0
                )
                car_record = schema_pb2.CarRecord(
                    id_compteur=record["iu_ac"],
                    nom_compteur=record["libelle"],
                    date=record["t_1h"],
                    etat_trafic=record["etat_trafic"],
                    coord=coordinates,
                    compteur_amont=record["iu_nd_amont"],
                    nom_compteur_amont=record["libelle_nd_amont"],
                    id_compteur_aval=record["iu_nd_aval"],
                    nom_compteur_aval=record["libelle_nd_aval"],
                )

                kafka_producer.produce(topic="car",
                        key=string_serializer("car","utf-8"),
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
        {"bootstrap.servers": "localhost:9092", "client.id": "producer"}
    )
    print("Sending bike records")
    bikeStream(bike_records, background_tasks, kafka_producer)
    print("Sending car records")
    carStream(car_records, background_tasks, kafka_producer)
    res = await asyncio.gather(*background_tasks)
    return res


asyncio.run(main())
