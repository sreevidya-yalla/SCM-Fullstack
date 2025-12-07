import json
import random
import asyncio
import os
from aiokafka import AIOKafkaProducer
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "device-stream-topic")

MONGO_URI = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URI)
db = client["SCM"]
devices = db["devices"]

async def main():
    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )

    while True:
        try:
            await producer.start()
            print("📤 Kafka Producer Started")
            break
        except Exception as e:
            print("Retrying Kafka Producer Connection...", e)
            await asyncio.sleep(5)

    routes = ["Newyork,USA", "Chennai, India", "Bengaluru, India", "London,UK"]

    while True:
        assigned_devices = await devices.find({"status": "assigned"}, {"_id": 0}).to_list(None)
        for dev in assigned_devices:
            data = {
                "Device_ID": dev["device_id"],
                "Battery_Level": round(random.uniform(2.00, 5.00), 2),
                "First_Sensor_temperature": round(random.uniform(10.0, 40.0), 1),
                "Route_From": random.choice(routes),
                "Route_To": random.choice(routes),
            }

            while data["Route_From"] == data["Route_To"]:
                data["Route_To"] = random.choice(routes)

            try:
                await producer.send_and_wait(TOPIC, data)
                print("Produced:", data)
            except Exception as e:
                print("Kafka Send Error:", e)

        await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
