import configparser


def read_config(section, option, default=None, value_type=str):
    config = configparser.ConfigParser()
    config.read("config.ini")

    try:
        if value_type == bool:
            return config.getboolean(section, option, fallback=default)
        elif value_type == int:
            return config.getint(section, option, fallback=default)
        elif value_type == float:
            return config.getfloat(section, option, fallback=default)
        else:
            return config.get(section, option, fallback=default)
    except (configparser.NoSectionError, configparser.NoOptionError):
        return default
