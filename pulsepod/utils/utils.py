# Lots of stuff to import. 
import struct
import json
import time
import struct
from  pulsepod.utils import cfg
from flask import current_app as app
from flask import jsonify
import requests
import werkzeug.exceptions
from random import choice, randint
from names import firstnames, lastnames


# Definie a exception class to report errors (handy for debugging)
class InvalidMessage(Exception):
	"""Raised when pdu2json cannot properly format the PDU submitted
    :param pdu_exception: the original exception raised by pdu2json
	"""
	status_code = 400
	def __init__(self, error, status_code=None, payload=None):
		Exception.__init__(self) 
		self.error = error
		if status_code is not None:
			self.status_code = status_code
		self.payload = payload
	
	def to_dict(self):
		rv = dict(self.payload or ())
		rv['error'] = self.error
		return rv
	
def pod_name():
	return choice(firstnames) + '-' + choice(lastnames) + '-' + str(randint(1000,9999))

##############################################
# PARSING UTILITIES 						 #
##############################################
def get_sensor(sid):
	sensor = {}
	try:
		s = requests.get(cfg.API_URL + '/sensors/?where={"sid":	' + str(sid) + "}")
	except:
		raise InvalidMessage('Unable to contact the API [sensors]',status_code=503) 
	if not s.status_code == requests.codes.ok:
		raise InvalidMessage('API unable to determine sensor information',\
			 				status_code=400,payload={'status_code':r.status_code})
	
	# sensor data is packed as a dict, but through a couple of layers
	try:
		resp = s.json()["_items"][0]
	except:
		raise InvalidMessage('sid not found',status_code=400)
			
	try:
		sensor['value_length'] = resp[u'nbytes']
		sensor['name'] = resp[u'name'] 
		sensor['_id'] = resp[u'_id']
		sensor['fmt'] = resp[u'byteorder'] + resp[u'fmt'] 
	except:
		raise InvalidMessage('Error reading sid',status_code=400)

	return sensor

def get_time(content,i):
	#parse unixtime to long int, then convert to database time
	try:
		unixtime = struct.unpack('<L', content[i:i+8].decode('hex'))[0]
	except:
		raise InvalidMessage('Error decoding timestamp',status_code=400)
	t = time.gmtime(unixtime)
	#dbtime is (e.g.) "Tue, 17 Sep 2013 01:33:56 GMT"
	dbtime = time.strftime("%a, %d %b %Y %H:%M:%S GMT", t)
	return dbtime

def get_value(content,i,sensor):
	# parse value based on format string
	try:
		value = struct.unpack(str(sensor['fmt']), content[i:i+(2*int(sensor['value_length']))].decode('hex'))[0]
	except:
		raise InvalidMessage('Error parsing format string',status_code=400)
				
	# Right here we would do some initial QA/QC based on whatever 
	# QA/QC limits we eventually add to the sensor specifications.
	return float(value)

# Data posting utilities
def update_voltage(message):
	v = next((item for item in message.data if item["sensor"] == "525ebfa0f84a085391000495"), None)
	# But we need to extract the vbatt_tellit out of the data blob. 
	# Use the Sensor Id, which should be relatively constant. HACKY! 
	if v:
		podupdate={}
		podupdate["last"] = v["t"]
		podupdate["voltage"] = v["v"]
		# Don't forget to set the content type, because it defaults to html
		thispod = podurl + "/" + str(message.pod['_id'])				
		headers= {'If-Match':str(message.pod[cfg.ETAG]),'content-type':'application/json'}
		u = requests.patch(thispod,data=json.dumps(podupdate),headers=headers)
		# Need to have some graceful failures here... Response Code? HACKY!
		return u.status_code
	else: 
		return None	

def get_notebook(nid):
	# This function will return a notebook JSON object from the API
	# It takes a nid object, which is of the form:
	# {'field':'value'}, where 'field' is '_id'.
	HEADERS = {'content-type':'application/json'} # Headers for the requests call
	pass




