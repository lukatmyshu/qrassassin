import hashlib
import logging
import os
import urllib
import urlparse

from google.appengine.api import users
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util, template

from models import *
from util import *

class DefaultHandler(webapp.RequestHandler):
    def post(self):
        assassin_id = self.request.get("assassin")
        target_id = self.request.get("target")

        q = db.GqlQuery("SELECT * FROM Assassin WHERE :id = :1", assassin_id)
        results = q.fetch(1)
        assassin = results[0]

        q = db.GqlQuery("SELECT * FROM Assassin WHERE :id = :1", target_id)
        results = q.fetch(1)
        target = results[0]

        path = os.path.join(os.path.dirname(__file__), 'admin.html')
        self.response.out.write(template.render(path, dict(assassins=results)))
