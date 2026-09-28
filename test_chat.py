import requests

url = "https://f39495b1a937cd.lhr.life/chat"

# Create a small valid webm file
with open("test.webm", "wb") as f:
    f.write(b"") 

response = requests.post(url, files={"audio": open("test.webm", "rb")})
print(response.status_code)
print(response.text)
