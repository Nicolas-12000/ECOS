from pyspark.sql import SparkSession
import os

os.environ['PYSPARK_PYTHON'] = 'py'
os.environ['PYSPARK_DRIVER_PYTHON'] = 'py'

spark = SparkSession.builder.appName("test").getOrCreate()
df = spark.createDataFrame([(1, "A"), (2, "B")], ["id", "val"])
df.show()
spark.stop()
