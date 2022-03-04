import base64, requests, configparser, logging

# image transfer via REST
logging.debug( 'Start image transfer' )
requestData = {}

requestData = {
    'stationName': 'ROCLUJObservatory',
    'stationId': 'RO001',
    'sundialName': 'Observatorul Astronomic Cluj-Napoca',
    'location': 'Cluj-Napoca, Cluj, Romania',
    'latitude': 46.757731,
    'longitude': 23.586472,
    'webcamType': 'RaspberryPI+Cam',
    'transferType': 'RaspberryPI',
    'sundialInfo': 'The sundial was constructed by Miholcsa Gyula in 2017. Hours read LAT + longitude correction/DST. Dotted line marks local noon.',
    'websiteUrl': 'https://astronomieculturala.ro, https://ubbcluj.ro',
    'teamName': 'Dan-George Uza, Mihai Cuibus, Hans Johrend',
    'nearbyPublicInstitute': 'Observatorul Astronomic Cluj-Napoca, Str. Ciresilor nr. 19, Cluj-Napoca, 400487, RO',
    'organizationalForm': 'Societatea Romana pentru Astronomie Culturala'
}

imgTotal_base64 = ''
with open('C:/earthlat/' + requestData['stationId'] + '/imgtotal.jpg', 'rb') as image_file:
	imgTotal_base64 = base64.b64encode(image_file.read()).decode('utf-8')
requestData['imgTotal'] = imgTotal_base64

imgDetail_base64 = ''
with open('C:/earthlat/' + requestData['stationId'] + '/imgdetail.jpg', 'rb') as image_file:
	imgDetail_base64 = base64.b64encode(image_file.read()).decode('utf-8')
requestData['imgDetail'] = imgDetail_base64

requestData['Status'] = {
	'swVersion': "Version 0.1",
	'captureTime': "UTC: ...",
	'captureLat': "LAT: ...",
	'cpuTemparature': 50.0,
	'cameraTemparature': 20.0,
	'outcaseTemparature': 20.0,
	'brightness': 10,
	'sunny': 1,
	'cloudy': 0,
	'night': 0
}

route = 'https://staging-earth-lat-1200-api.azurewebsites.net/api/%s/Push' % requestData['stationId']
headers = {'x-functions-key': 'MyQuFbkVvtpRFZ6goLzmwdNjwSGnUhIYx89emvCEG8PSF5vJdBaooQ=='}
response = requests.post(route, json=requestData, headers=headers)
print(response)
responseData = response.json()["value"]
print(responseData)
