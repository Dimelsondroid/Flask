import requests

response = requests.post('http://127.0.0.1:5000/user',
                         json={'username': 'admin_again', 'password': '123123123'})

print(response.status_code)
print(response.json())

response = requests.get('http://127.0.0.1:5000/user/2', )
#                          json={'username': 'admin_again', 'password': '123123123'})

print(response.status_code)
print(response.text)

response = requests.post('http://127.0.0.1:5000/user/2/adv',
                         json={'headline': 'new adv on my car', 'description': 'still selling'})

print(response.status_code)
print(response.json())
#
response = requests.post('http://127.0.0.1:5000/user/1/adv',
                         json={'headline': 'new adv on my car', 'description': 'still selling'})

print(response.status_code)
print(response.json())
#
response = requests.delete('http://127.0.0.1:5000/adv/2', )

print(response.status_code)
print(response.json())