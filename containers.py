from dependency_injector import containers
from service import Service
from config import Config


class ApplicationContainer(containers.DeclarativeContainer):
    service = Service(Config.env)
