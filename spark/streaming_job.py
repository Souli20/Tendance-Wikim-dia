from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, IntegerType, BooleanType
)

KAFKA_SERVER = "localhost:9092"
TOPIC = "wiki-changes"

spark = SparkSession.builder.appName("WikimediaTrends").master("local[2]").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

schema = StructType([
    StructField("id", LongType()),
    StructField("wiki", StringType()),
    StructField("title", StringType()),
    StructField("namespace", IntegerType()),
    StructField("type", StringType()),
    StructField("user", StringType()),
    StructField("bot", BooleanType()),
    StructField("timestamp", LongType()),
])

brut = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_SERVER)
    .option("subscribe", TOPIC)
    .option("startingOffsets", "latest")
    .load()
)

evenements = (
    brut.select(from_json(col("value").cast("string"), schema).alias("e"))
    .select("e.*")
    .withColumn("event_time", col("timestamp").cast("timestamp"))
)

requete = (
    evenements.select("wiki", "title", "user", "bot", "event_time")
    .writeStream.format("console")
    .outputMode("append")
    .option("truncate", False)
    .start()
)
requete.awaitTermination()
