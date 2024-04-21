# https://stackoverflow.com/questions/19434947/python-respond-to-http-request
# LOOK AT .write() HERE: https://gist.github.com/mendhak/eb22f70adf0f7e694bbcb4ef0b11b5a8


# Info on Alexa protocol:
#    https://developer.amazon.com/en-US/docs/alexa/custom-skills/request-and-response-json-reference.html


#import SocketServer
#from BaseHTTPServer import BaseHTTPRequestHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import os
import tempfile
import sys
import time
from datetime import datetime
import signal
import threading
import json
import time

DEBUG=False

ICECAST_URL="https://stream.asklab.net/access-icecast.php"
version="1.0"

def shutdownEverything():
	httpd.shutdown()

	httpd.socket.close()

def terminateProcess(signalNumber, frame):
	shutdownEverything()
	sys.exit(0)

def getTempFile():
    f,fname = tempfile.mkstemp()
    os.close(f)
    return fname

"""
      let slot = getSlotValues(requestEnvelope);
      let station = collection.get(slot.station);

      if (station.name) {
        Alexa.sessionAttributes = { token: station };
        Alexa
          //.speak(`${now_playing} ${station.name} from ${station.channel}.`)
          .speak(`playing your stream`)
          .play(user_url, station.url, station.progress, station.token)

    if (token) {
      station = token.split(':')[0];
      channel = token.split(':')[1];
    } else {
      token = " "
    }


    offset=0; // Sometimes we receive *huge* numbers from the caller. I don't think this is a real offset

      token = " "
    console.log("in play(): using url "+url+"; token="+token+"; offset="+offset);

"""

# https://stackoverflow.com/questions/23264569/python-3-x-basehttpserver-or-http-server
class MyHandler(BaseHTTPRequestHandler):
	timeout = 5    # kill connection after 5 seconds

	def playRadioIntentHandler(self,j):
		station_info=j['request']['intent']['slots']['station']
		offset=0
		if 'token' in station_info:
			token=station_info['token']
			station=token.split(':')[0]
			channel=token.split(':')[1]
		else:
			token=" "
			station="station"
			channel=""

		url=ICECAST_URL+"?rnd="+str(int(time.time() * 1000))

		data={
			"version": version,
			"sessionAttributes": {
				"token": station
			},
			"response": {
				"outputSpeech": {
					"type": "PlainText",
					"text": "Playing your stream",
					"playBehavior": "REPLACE_ENQUEUED"
					},
				"directives": [{
						"type": "AudioPlayer.Play",
						"playBehavior": "REPLACE_ALL",
						"audioItem": {
							"stream": {
							"url": url,
							"token": token,
							"offsetInMilliseconds": offset
							},
							"metadata": {
								"title": station,
								"subtitle": channel
							}
						}
					}],
				"shouldEndSession": True
				}
			}
		return data

	def stopIntentHandler(self,j):
		data={
			"version": version,
			"response": {
				"outputSpeech": {
					"type": "PlainText",
					"text": "Stopping the stream",
					"playBehavior": "REPLACE_ENQUEUED"      
					},
				"directives": [{
						"type": "AudioPlayer.Stop",
					}],
				"shouldEndSession": True
				}
			}
		return data

	def unknownIntentHandler(self,j):
		data={
			"version": version,
			"response": {
				"shouldEndSession": True
				}
			}
		return data


	def do_POST(self):
		# test with: curl -d "test1" -X POST http://localhost:8015
		# Also:  curl -d "test1" -X POST https://dssresearch.sju.edu/clingo/
		#print("received POST request:",self.path)
		#print("HEADERS")
		#print(self.headers)
		#print("BODY")
		content_len = int(self.headers.get('Content-Length'))
		post_body = self.rfile.read(content_len)
		#print(f'post_body={post_body}')
		j=json.loads(post_body)
		#print(j)
		print(j['request'])
		data=None
		if j['request']['type']=="IntentRequest":
			if j['request']['intent']['name']=='PlayRadioIntent':
				data=self.playRadioIntentHandler(j)
			elif j['request']['intent']['name']=='AMAZON.StopIntent':
				data=self.stopIntentHandler(j)
			elif j['request']['intent']['name']=='AMAZON.PauseIntent':
				data=self.stopIntentHandler(j)
			elif j['request']['intent']['name']=='AMAZON.CancelIntent':
				data=self.stopIntentHandler(j)
		if data is None:
			data=self.unknownIntentHandler(j)

		self.send_response(200)
		self.send_header("Content-type", "application/json;charset=UTF-8")
		self.end_headers()
		self.wfile.write(bytes(json.dumps(data), "utf-8"))
#		else:
#			self.send_error(404)
#			return



signal.signal(signal.SIGINT, terminateProcess)
signal.signal(signal.SIGQUIT, terminateProcess)
signal.signal(signal.SIGINT, terminateProcess)
signal.signal(signal.SIGTRAP, terminateProcess)
signal.signal(signal.SIGABRT, terminateProcess)
#signal.signal(signal.SIGILL, receiveSignal)
#signal.signal(signal.SIGTRAP, receiveSignal)
#signal.signal(signal.SIGABRT, receiveSignal)
#signal.signal(signal.SIGBUS, receiveSignal)
#signal.signal(signal.SIGFPE, receiveSignal)
#signal.signal(signal.SIGKILL, receiveSignal)  # cannot be caught in Python
#signal.signal(signal.SIGUSR1, receiveSignal)
#signal.signal(signal.SIGSEGV, receiveSignal)
#signal.signal(signal.SIGUSR2, receiveSignal)
#signal.signal(signal.SIGPIPE, receiveSignal)
#signal.signal(signal.SIGALRM, receiveSignal)
signal.signal(signal.SIGTERM, terminateProcess)

HTTPServer.allow_reuse_address = True
httpd = HTTPServer(("", 14880), MyHandler)
try:
	print("Waiting for requests...")
#	httpd.serve_forever()
	thread = threading.Thread(None, httpd.serve_forever)
	thread.start()
	thread.join()
except KeyboardInterrupt:
	shutdownEverthing()


#q="What is Saint Joseph's University?"
#print("Asking: "+q)
#print(query_GPT(q,"gpt-3.5-turbo")) #,'text-davinci-003'))

#with open('response.txt', 'w+', encoding="utf-8") as f:
#    f.write(Response['choices'][0]['text']) #Writes response to a txt file that will be contained in the same folder as this file
