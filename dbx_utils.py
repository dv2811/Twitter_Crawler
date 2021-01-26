# -*- coding':'utf-8 -*-
from requests import get,post
import json
#from openpyxl import load_workbook
from io import BytesIO

token = 'FTU-AKgRtwoAAAAAAAAAAVJ-I4jAbDGH8yqx0IaXJyVQ6Fu3tYfC606lv3vLtYPL'
headers = {	'Authorization': 'Bearer '+token, }
def dbx_read(path):
	headers.update( {'Dropbox-API-Arg':json.dumps({'path': path}) } )
	response=post('https://content.dropboxapi.com/2/files/download',headers=headers)
	if response.status_code==200:
		return response.text
	else:
		return ''

def dbx_upload(file_content,path):
	headers = {
	'Authorization': 'Bearer '+token,
	'Dropbox-API-Arg':json.dumps({'path': path, 'mode': 'overwrite', 'autorename': True, 'mute': False, 'strict_conflict': False}),
	'Content-Type':'application/octet-stream',
	}
	response = post("https://content.dropboxapi.com/2/files/upload", headers=headers, data=file_content)

	if response.status_code!=200:
		print (response.text)
		print ('Upload '+path+' unsuccessful!')
