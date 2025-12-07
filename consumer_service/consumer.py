import json
import asyncio
import os
from aiokafka import AIOKafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "device-stream-topic")
GROUP_ID = os.getenv("KAFKA_CONSUMER_GROUP", "device-stream-group")

MONGO_URI = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URI)
db = client["SCM"]
device_stream_collection = db["device_stream"]

async def main():
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP_ID,
        auto_offset_reset="latest",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )

    while True:
        try:
            await consumer.start()
            print("📥 Kafka Consumer Started")
            break
        except Exception as e:
            print("Retrying Kafka Consumer Connection...", e)
            await asyncio.sleep(5)

    try:
        async for msg in consumer:
            data = msg.value
            print("Received:", data)
            await device_stream_collection.insert_one(data)
            print("Saved to MongoDB")

    finally:
        await consumer.stop()
        print("Kafka Consumer Stopped")

if __name__ == "__main__":
    asyncio.run(main())
