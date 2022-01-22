class Service:
    def __init__(self, env: str):
        self.APP_ENV = env

    def get_env(self):
        return self.APP_ENV