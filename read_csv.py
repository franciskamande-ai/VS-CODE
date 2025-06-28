import requests

url = "https://v6.exchangerate-api.com/v6/caa4b53d5c599f5dd44a0700/latest/USD"
response = requests.get(url)

data = response.json()
print("Here is the data from the API:")
print(data)
