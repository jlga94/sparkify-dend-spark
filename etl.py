import configparser
from datetime import datetime
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.functions import year, month, dayofmonth, hour, weekofyear, date_format
from pyspark.sql.types import TimestampType
from pyspark.sql.functions import to_timestamp,monotonically_increasing_id

config = configparser.ConfigParser()
config.read('dl.cfg')

os.environ['AWS_ACCESS_KEY_ID']=config.get('AWS_CREDENTIALS','AWS_ACCESS_KEY_ID')
os.environ['AWS_SECRET_ACCESS_KEY']=config.get('AWS_CREDENTIALS','AWS_SECRET_ACCESS_KEY')


def create_spark_session():
    """This function will create the spark session that will be available all the session."""
    spark = SparkSession \
        .builder \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:2.7.0") \
        .getOrCreate()
    return spark


def process_song_data(spark, input_data, output_data):
    """This function will ingest the data from the song_data path. Also will create the parquets files for the songs table and artist table."""
    # get filepath to song data file
    song_data = input_data + "song_data/*/*/*/*.json"
    
    # read song data file
    df = spark.read.json(song_data)

    # extract columns to create songs table
    songs_table = df.select("song_id","title", "artist_id","year","duration").dropDuplicates()
    
    # write songs table to parquet files partitioned by year and artist
    songs_table.write.mode("overwrite").partitionBy("year","artist_id").parquet(output_data+"songs")

    # extract columns to create artists table
    artists_table = df.select("artist_id",col("artist_name").alias("name"),col("artist_location").alias("location"),col("artist_latitude").alias("latitude"),col("artist_longitude").alias("longitude")).dropDuplicates()

    # write artists table to parquet files
    artists_table.write.mode("overwrite").parquet(output_data+"artists")


def process_log_data(spark, input_data, output_data):
    """This function will ingest the data from the log-data path. Also will create the parquets files for the users table and the time table. In the case of the songplays table, it will be joined with the data from the song_path."""
    
    # get filepath to log data file
    log_data = input_data + "log-data"

    # read log data file
    df = spark.read.json(log_data)
    
    # filter by actions for song plays
    df = df.filter(col("page")=='NextSong').filter(df.userId.isNotNull())

    # extract columns for users table    
    users_table = df.select(col("userId").alias("user_id"), col("firstName").alias("first_name"), col("lastName").alias("last_name"), "gender", "level").dropDuplicates()
    
    # write users table to parquet files
    users_table.write.mode("overwrite").parquet(output_data+"users")

    # create timestamp column from original timestamp column
    get_timestamp = udf(lambda x: str(int(int(x) / 1000)))
    df = df.withColumn("timestamp",get_timestamp(col("ts")))
    
    # create datetime column from original timestamp column
    get_datetime = udf(lambda x: str(datetime.fromtimestamp(int(x) / 1000.0)))
    df = df.withColumn("datetime", get_datetime(col("ts")))
    
    # extract columns to create time table
    time_table = df.select(
         'timestamp',
         hour('datetime').alias('hour'),
         dayofmonth('datetime').alias('day'),
         weekofyear('datetime').alias('week'),
         month('datetime').alias('month'),
         year('datetime').alias('year'),
         date_format('datetime', 'F').alias('weekday')
     )
    
    # write time table to parquet files partitioned by year and month
    time_table.write.mode("overwrite").partitionBy("year","month").parquet(output_data+"time")

    # read in song data to use for songplays table
    song_data = input_data + "song_data/*/*/*/*.json"
    song_df = spark.read.json(song_data)

    # extract columns from joined song and log datasets to create songplays table 
    tsFormat = "yyyy/MM/dd HH:MM:ss z"
    songplays_table = song_df.join(df,song_df.artist_name==df.artist).withColumn("songplay_id", monotonically_increasing_id()).withColumn('start_time', to_timestamp(date_format((col("ts") /1000).cast(dataType=TimestampType()), tsFormat),tsFormat)).select("songplay_id","start_time",col("userId").alias("user_id"),"level","song_id","artist_id",col("sessionId").alias("session_id"),col("artist_location").alias("location"),"userAgent",month(col("start_time")).alias("month"),year(col("start_time")).alias("year"))


    # write songplays table to parquet files partitioned by year and month
    songplays_table.write.mode("overwrite").partitionBy("year","month").parquet(output_data+"songplays")


def main():
    """This is the main function that will create the spark session and create the dataframes that will be written in parquet in S3."""
    spark = create_spark_session()
    input_data = "s3a://udacity-dend/"
    output_data = ""
    
    process_song_data(spark, input_data, output_data)    
    process_log_data(spark, input_data, output_data)


if __name__ == "__main__":
    main()
