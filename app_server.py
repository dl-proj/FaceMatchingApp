import configparser

from settings import CONFIG_FILE_PATH
from src.server.age_system import AgeSystem


if __name__ == '__main__':

    param_file = CONFIG_FILE_PATH
    params = configparser.ConfigParser()
    params.read(param_file)

    AgeSystem(parameters=params).main()
