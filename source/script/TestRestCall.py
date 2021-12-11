import requests
import base64
import configparser

config = configparser.ConfigParser()
config.read('script/stationinfo.txt')

imgTotal_base64 = ''
imgDetail_base64 = ''
with open('imgtotal.jpg', 'rb') as image_file:
    imgTotal_base64 = base64.b64encode(image_file.read()).decode('utf-8')
with open('imgdetail.jpg', 'rb') as image_file:
    imgDetail_base64 = base64.b64encode(image_file.read()).decode('utf-8')

jsonMessage = {
	'imgTotal' : 'base64',
	'imgDetail' : 'base64',
	'stationInfo' : {
		'header' : {
			'idName': 'AT101',
			'idNo': 'SDC_Developer'
		},
		'info': {
			'name': 'Developer Station',
			'location': 'City, Country',
			'latitude' : 48.30,
			'longitude' : 10.00,
			'typeWebCam' : 'RaspberryPI+Cam',
			'typeTransfer' : 'RaspberryPI',
			'text' : 'A short description of the sundial, the local project, another interesting details.',
			'website' : 'Website',
			'team' : 'local members',
			'nearbyPublicInst' : 'Great Public Building, anywhere',
			'organization' : 'What is the organization of the team'
		}
	},
	'status' : {
       'System' : {
			'swversion' : 0,
			'capturetime' : 0,
			'capturelat' : 0,
			'cputemperature' : 0,
			'cameratemperature' : 0,
			'outcasetemperature' : 0 
		},
        'Dial' : {
			'brightness' : 0,
            'sunny' : 0,
            'cloudy' : 0,
            'night' : 0
		}
	}
}

possibleResponse = '''
{
	'command': {
		'camOffline': 0,
		'periodM': 0,
		'series': 0,
		'zoomMove': 0,
		'zoomDrawRect': 0
	},
	'detail': {
		'zoomCentPercX': 0,
		'zoomCentPercY': 0
	}
}
'''

#key = ''
#route = 'http://localhost:7071/api/transfer-images/%s' % key'
route = 'https://httpbin.org/anything'
response = requests.put(route, json=jsonMessage)
responseData = response.json()['data']

print('data:\n%s' % responseData)