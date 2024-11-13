from nldcsc.plugins.redis_client.wrapper import RedisWrapper


class FlaskRedis(RedisWrapper):
    def __init__(
        self, app=None, init_standalone: bool = False, redis_url: str = None, **kwargs
    ):
        if app and init_standalone:
            raise Exception("App must be None when 'init_standalone' is set to True")
        
        super().__init__(redis_url=redis_url, auto_connect=False, **kwargs)

        if app is not None or init_standalone:
            self.init_app(app)

    def init_app(self, app, **kwargs):
        self.kwargs.update(kwargs)
        self.connect()

        if app is not None:
            app.redis_client = self

    def __repr__(self):
        return "<< FlaskRedis >>"
