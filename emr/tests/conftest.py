import os

import pytest
from pyspark.sql import SparkSession
import requests
from mockito import unstub, verifyStubbedInvocationsAreUsed


@pytest.fixture(scope="function", autouse=True)
def mockito_unstub():
    """After every unit test, verifies mockito stubs are used and un-stubs them."""
    yield
    try:
        verifyStubbedInvocationsAreUsed()
    finally:
        unstub()


@pytest.fixture(scope="session")
def spark(tmpdir_factory):
    """Local SparkSession instance for testing Spark jobs.

    scope="session" allows this SparkSession instance to be shared
    across all unit tests.
    """

    additional_libs_path = tmpdir_factory.mktemp('libs')
    spark_avro_path = _download_spark_avro(additional_libs_path.strpath)

    spark = SparkSession.builder \
        .master("local[2]") \
        .appName("unit-tests") \
        .enableHiveSupport() \
        .config("spark.sql.session.timeZone", "UTC") \
        .config('spark.jars', spark_avro_path) \
        .getOrCreate()

    yield spark

    # Cleanup after all tests are finished
    spark.stop()


def _download_spark_avro(dir_path: str) -> str:
    url = 'https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.11/2.4.4/spark-avro_2.11-2.4.4.jar'
    r = requests.get(url, allow_redirects=True)
    file_path = os.path.join(dir_path, 'spark-avro_2.11-2.4.4.jar')
    open(file_path, 'wb').write(r.content)
    return file_path
