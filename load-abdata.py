from __future__ import absolute_import
import argparse
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
import os

#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/Users/praveen/Documents/code/kaggle-abnb-nyc-dataflow/bamboo-mercury-335312-85be2736674c.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/praveen_ponna/ab_nyc/bamboo-mercury-335312-85be2736674c.json"

class DataIngestion:
    def parse_method(self, string_input):
        values = re.split(",",
                          re.sub('\r\n', '', re.sub(u'"', '', string_input)))
        row = dict(
            zip(('id', 'name', 'host_id', 'host_name', 'neighbourhood_group', 'neighbourhood', 'latitude', 'longitude',
                 'room_type', 'price', 'minimum_nights', 'number_of_reviews', 'last_review', 'reviews_per_month',
                 'calculated_host_listings_count', 'availability_365'),
                values))
        return row

def run(argv=None):
    """The main function which creates the pipeline and runs it."""

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--input',
        dest='input',
        required=False,
        help='Input file to read. This can be a local file or '
        'a file in a Google Storage Bucket.',
        default='gs://bamboo-mercury-335312-kaggle/AB_NYC_2019.csv')

    # This defaults to the ab_nyc dataset in your BigQuery project. You'll have
    # to create the lake dataset yourself using this command:
    # bq mk ab_nyc
    parser.add_argument('--output',
                        dest='output',
                        required=False,
                        help='Output BQ table to write results to.',
                        default='ab_nyc.ab_data')

    # Parse arguments from the command line.
    known_args, pipeline_args = parser.parse_known_args(argv)

    # DataIngestion is a class we built in this script to hold the logic for
    # transforming the file into a BigQuery table.
    data_ingestion = DataIngestion()

    # Initiate the pipeline using the pipeline arguments passed in from the
    # command line. This includes information such as the project ID and
    # where Dataflow should store temp files.
    p = beam.Pipeline(options=PipelineOptions(pipeline_args))

    (
     p | 'Read from a File' >> beam.io.ReadFromText(known_args.input,
                                                  skip_header_lines=1)
     # This stage of the pipeline translates from a CSV file single row
     # input as a string, to a dictionary object consumable by BigQuery.
     # It refers to a function we have written. This function will
     # be run in parallel on different workers using input from the
     # previous stage of the pipeline.
     | 'String To BigQuery Row' >>
     beam.Map(lambda s: data_ingestion.parse_method(s))
     | 'Write to BigQuery' >> beam.io.Write(
         beam.io.BigQuerySink(
             # The table name is a required argument for the BigQuery sink.
             # In this case we use the value passed in from the command line.
             known_args.output,
             # Here we use the simplest way of defining a schema:
             # fieldName:fieldType

             schema='id:INTEGER,name:STRING,host_id:INTEGER,host_name:STRING,neighbourhood_group:STRING,'
                    'neighbourhood:STRING,latitude:FLOAT,longitude:FLOAT,room_type:STRING,price:FLOAT,'
                    'minimum_nights:INTEGER,number_of_reviews:INTEGER,last_review:DATE,reviews_per_month:INTEGER,'
                    'calculated_host_listings_count:INTEGER,availability_365:INTEGER',

             # Creates the table in BigQuery if it does not yet exist.
             create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
             # Deletes all data in the BigQuery table before writing.
             write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE)))
    p.run().wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()