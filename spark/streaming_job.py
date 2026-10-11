from datetime import timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType, IntegerType, BooleanType
)

KAFKA_SERVER = "localhost:9092"
TOPIC = "wiki-changes"

spark = SparkSession.builder.appName("WikimediaTrends").master("local[2]").config("spark.sql.session.timeZone", "UTC").getOrCreate()
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

from pyspark.sql.functions import window, count, approx_count_distinct, sum as somme, when

articles = evenements.filter(
    (col("namespace") == 0)
    & (col("wiki") != "wikidatawiki")
    & (col("type").isin("edit", "new"))
)

par_minute = (
    articles.withWatermark("event_time", "2 minutes")
    .groupBy(window(col("event_time"), "1 minute"), col("wiki"), col("title"))
    .agg(
        count("*").alias("nb_modifs"),
        approx_count_distinct("user").alias("nb_editeurs"),
        somme(when(col("bot"), 1).otherwise(0)).alias("nb_bots"),
    )
)

from pymongo import MongoClient, ReplaceOne


def ecrire_dans_mongo(lot, id_lot):
    lignes = lot.collect()
    if not lignes:
        return
    collection = MongoClient("mongodb://localhost:27017")["wiki_db"]["trends_per_minute"]
    operations = []
    for ligne in lignes:
        debut = ligne["window"]["start"].astimezone(timezone.utc)
        document = {
            "_id": f'{debut.isoformat()}|{ligne["wiki"]}|{ligne["title"]}',
            "window_start": debut,
            "window_end": ligne["window"]["end"].astimezone(timezone.utc),
            "wiki": ligne["wiki"],
            "title": ligne["title"],
            "nb_modifs": ligne["nb_modifs"],
            "nb_editeurs": ligne["nb_editeurs"],
            "nb_bots": ligne["nb_bots"],
        }
        operations.append(ReplaceOne({"_id": document["_id"]}, document, upsert=True))
    collection.bulk_write(operations)
    print("Lot", id_lot, ":", len(operations), "lignes écrites dans MongoDB")

requete = (
    par_minute.writeStream.outputMode("update")
    .foreachBatch(ecrire_dans_mongo)
    .start()
)
requete.awaitTermination()
