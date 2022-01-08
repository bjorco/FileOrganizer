import configparser

def generate_config():
    conf = configparser.ConfigParser()
    conf['SERIES'] = {
        'NAME': 'ZK',
        'NUMBER': 23412 
    }

    conf['SOURCES'] = {}
    conf['DESTINATIONS'] = {}

    with open('mapping.ini', 'w') as configfile:
        conf.write(configfile)

generate_config()