"""
PySpark + Spark NLP message processing pipeline (Phase 2).
Reads from Kafka patient_messages topic, processes text, outputs sentiment/risk scores.

Run: spark-submit message_pipeline.py
"""
import os
import json

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = "patient_messages"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://echosense:echosense@localhost:5432/echosense")


def process_batch(batch_df, batch_id):
    """Process each micro-batch of messages."""
    rows = batch_df.collect()
    for row in rows:
        text = row.get("content", "") if hasattr(row, "get") else getattr(row, "content", "")
        if not text:
            continue
        text_lower = text.lower()
        negative_words = ["sad", "hopeless", "anxious", "die", "hurt", "suicide"]
        hits = sum(1 for w in negative_words if w in text_lower)
        sentiment_score = min(1.0, 0.3 + hits * 0.15)
        sentiment_label = "negative" if sentiment_score > 0.6 else "neutral"
        print(json.dumps({
            "batch_id": batch_id,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "processed": True,
        }))


def main():
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import from_json, col
        from pyspark.sql.types import StructType, StructField, StringType, IntegerType
    except ImportError:
        print("PySpark not installed. Install with: pip install pyspark")
        return

    spark = (
        SparkSession.builder.appName("EchoSenseMessagePipeline")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
        .getOrCreate()
    )

    schema = StructType([
        StructField("patient_id", IntegerType()),
        StructField("content", StringType()),
    ])

    df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    parsed = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")
    query = parsed.writeStream.foreachBatch(process_batch).outputMode("append").start()
    query.awaitTermination()


if __name__ == "__main__":
    main()
