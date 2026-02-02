import json

def load_settings(filePath='RPI1/settings/settings.json'):
    with open(filePath, 'r') as f:
        return json.load(f)