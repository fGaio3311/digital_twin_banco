import requests
import json

try:
    # Teste de conexão
    r = requests.get('http://localhost:8000/ping')
    print(f'Ping: {r.status_code}')

    # Criar conta
    r = requests.post('http://localhost:8000/register', json={'username': 'test123', 'password': 'test123'})
    print(f'Register: Status {r.status_code}, Response: {r.text}')

    # Fazer login
    data = {'username': 'test123', 'password': 'test123'}
    r = requests.post('http://localhost:8000/token', data=data)
    print(f'Login: Status {r.status_code}, Response: {r.text}')

except Exception as e:
    print(f'Erro: {e}')
