import cgi
import webapp2
import os
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from datetime import datetime
import pytz
import twilio.twiml

MEMCACHE_FORECAST_KEY = "FORECAST"
MEMCACHE_DEPARTURE_KEY = "DEPARTURE"

class MainPage(webapp2.RequestHandler):
    def get(self):
    
        template_values = {
        	'forecast': memcache.get(MEMCACHE_FORECAST_KEY) or 'None available',
        	'departure' : memcache.get(MEMCACHE_DEPARTURE_KEY) or 'None available' 
        }

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

class PostForecast(webapp2.RequestHandler):
  def get(self):
    page = self.request.path[1:]
    template_values = {
            'content': '<body><br><h3>Forecast:</h3><p>{}</p><br><h3>Boat Times:</h3><p>{}</p></body>'.format(
              memcache.get(MEMCACHE_FORECAST_KEY) or 'Not available',
              memcache.get(MEMCACHE_DEPARTURE_KEY) or 'Not available'
              ),
            'content_id': page,
            }

    path = os.path.join(os.path.dirname(__file__), 'index.html' )

    self.response.out.write(template.render(path, template_values))

  def post(self):
    ''' handler for twilio text message based forecast '''
    resp = twilio.twiml.Response()
    tokens = self.request.POST['Body'].split('.')
    if tokens[0][0] == '@': #boat departure time
      hour = int(tokens[0][1:].split(':')[0])
      departure = "Downwinder boat is departing from Sherman Island boat ramp at {}{}".format(tokens[0][1:], ('AM', 'PM')[hour < 7])
      if tokens[1:]:
        departure += " with {} seat{} available".format(tokens[1], ('s', '')[int(tokens[1]) < 1])
      resp.message(departure)
      self.response.out.write(str(resp))
      memcache.set(MEMCACHE_DEPARTURE_KEY, departure)
      return

    forecast = "{:%b, %d at %H:%M} the wind is blowing {}MPH".format(datetime.now(pytz.timezone('US/Pacific')), tokens[0])
    for token in tokens[1:]:
      if token.startswith('-'):
        forecast += ', EBB tide starts at {}{}'.format(token[1:], ('AM', 'PM')[int(token[1:].split(':')[0]) < 7])
      else:
        forecast += ', FLOOD tide starts at {}{}'.format(token, ('AM', 'PM')[int(token.split(':')[0]) < 7])

    resp.message(forecast)
    self.response.out.write(str(resp))
    memcache.set(MEMCACHE_FORECAST_KEY, forecast)

app = webapp2.WSGIApplication([ ('/forecast', PostForecast),
								('/', MainPage)],
                      			debug=True)