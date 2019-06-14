# Data Lake with Spark: Song Play Analysis
> José Luis Gil Aguilar
## Project Summary

This ETL Pipeline was designed for a startup **Sparkify**, who wants to analyze the data comming from their songs and user activity on their new music streaming app. This project extracts their data from S3, processes them using Spark, and loads the data back into S3 as a set of dimensional tables using parquet files.

## Files in Project
Tha main files for running the project are:

* `dl.cfg`: which stores AWS credentials.
* `etl.py`: reads data from S3, processes that data using Spark, and writes them back to S3.

## How to run
1. Configure `dl.cfg` file with AWS credentials.
2. Run `python etl.py`