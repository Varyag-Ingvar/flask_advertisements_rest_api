import requests


HOST = 'http://127.0.0.1:5000'

'''test requests'''
# response = requests.post(f'{HOST}/ads/', json={'ad_name': 'sell iphone 7',
#                                                'ad_body': 'sell new brand iphone 7, used for 3 days',
#                                                'ad_owner': 'Vasya'})

response = requests.get(f'{HOST}/ads/3')

# response = requests.patch(f'{HOST}/ads/3', json={'ad_body': 'sell a tank t90, not an iphone'})

# response = requests.delete(f'{HOST}/ads/2')

print(response.status_code)
print(response.text)
