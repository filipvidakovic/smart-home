import json

def load_settings(filePath='RPI2/settings/settings.json'):
    with open(filePath, 'r') as f:
        return json.load(f)