import requests

r = requests.post('http://localhost:8000/test', json={"key": "value"})