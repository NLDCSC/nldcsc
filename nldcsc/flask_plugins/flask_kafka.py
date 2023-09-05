import json
import logging
import os

from kafka import KafkaProducer

from nldcsc.generic.utils import getenv_dict

# Effectively disabling the following loggers
logging.getLogger("kafka").setLevel(logging.CRITICAL)


class FlaskKafka(object):
    def __init__(self, app=None, **kwargs):
        self._producer = None
        self.kwargs = kwargs

        self.kafka_url = os.getenv("KAFKA_URL", "localhost:9092")
        self.kafka_kwargs = getenv_dict("KAFKA_KWARGS", None)

        if app is not None:
            self.init_app(app)

    def init_app(self, app, **kwargs):
        self.kwargs.update(kwargs)

        if self.kafka_kwargs is not None:
            self.kwargs.update(self.kafka_kwargs)

        self._producer = KafkaProducer(
            bootstrap_servers=self.kafka_url,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: json.dumps(k).encode("utf-8"),
            **self.kwargs,
        )

        if self.producer is not None:
            app.producer = self.producer

            if self.producer.bootstrap_connected():
                app.logger.info(f"Connected to KAFKA!!")
            else:
                app.logger.critical(f"Connection to KAFKA failed!! Could not connect!")

        else:
            app.logger.error(f"Connection to KAFKA failed!!, no producer set up...")

    @property
    def producer(self):
        return self._producer

    def __del__(self):
        if self.producer is not None:
            self.producer.close(5)

    def __repr__(self):
        return "<< FlaskKafka >>"
