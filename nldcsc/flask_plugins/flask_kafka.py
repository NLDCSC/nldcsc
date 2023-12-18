import json
import logging
import os

from kafka import KafkaProducer, KafkaConsumer

from nldcsc.generic.utils import getenv_dict

# Effectively disabling the following loggers
logging.getLogger("kafka").setLevel(logging.CRITICAL)


class FlaskKafka(object):
    def __init__(
        self, app=None, producer: bool = True, consumer: bool = True, **kwargs
    ):
        self._producer = None
        self._consumer = None

        self.create_producer = producer
        self.create_consumer = consumer
        self.kwargs = kwargs

        self.kafka_url = os.getenv("KAFKA_URL", "localhost:9092")
        self.kafka_kwargs = getenv_dict("KAFKA_KWARGS", None)

        if app is not None:
            self.init_app(app)

    def init_app(self, app, **kwargs):
        self.kwargs.update(kwargs)

        if self.kafka_kwargs is not None:
            self.kwargs.update(self.kafka_kwargs)

        if self.create_producer:
            self._producer = KafkaProducer(
                bootstrap_servers=self.kafka_url,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: json.dumps(k).encode("utf-8"),
                **self.kwargs,
            )

            if self.producer is not None:
                app.producer = self.producer

                if self.producer.bootstrap_connected():
                    app.logger.info(f"Producer connected to KAFKA!!")
                else:
                    app.logger.critical(
                        f"Connection to KAFKA failed!! Producer could not connect!"
                    )
            else:
                app.logger.error(f"Connection to KAFKA failed!!, no producer set up...")

        if self.create_consumer:
            self._consumer = KafkaConsumer(
                bootstrap_servers=self.kafka_url,
                value_deserializer=lambda v: json.dumps(v).encode("utf-8"),
                key_deserializer=lambda k: json.dumps(k).encode("utf-8"),
                auto_offset_reset="earliest",
                **self.kwargs,
            )

            if self.consumer is not None:
                app.consumer = self.consumer

                if self.consumer.bootstrap_connected():
                    app.logger.info(f"Consumer connected to KAFKA!!")
                else:
                    app.logger.critical(
                        f"Connection to KAFKA failed!! Consumer could not connect!"
                    )
            else:
                app.logger.error(f"Connection to KAFKA failed!!, no consumer set up...")

    @property
    def producer(self):
        return self._producer

    @property
    def consumer(self):
        return self._consumer

    def __del__(self):
        if self.producer is not None:
            self.producer.close(5)

        if self.consumer is not None:
            self.consumer.close(5)

    def __repr__(self):
        return "<< FlaskKafka >>"
