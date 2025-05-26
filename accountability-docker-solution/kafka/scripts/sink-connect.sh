#!/bin/sh

# ----- Sink to MongoDB

curl -s \
     -X "POST" "http://localhost:8083/connectors/" \
     -H "Content-Type: application/json" \
     -d '{
  "name": "mongo-sink",
  "config": {
     "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
        "tasks.max": "1",
        "topics": "ROSMessagesTopic",
        "connection.uri":"mongodb+srv://root:admin@cluster0.3b4os1l.mongodb.net",
        "database": "RealTimeRAG",
        "collection": "RealTimeRAG",
        "key.converter": "org.apache.kafka.connect.storage.StringConverter",
        "value.converter": "org.apache.kafka.connect.json.JsonConverter",
        "value.converter.schemas.enable": "false"
  }
}'
