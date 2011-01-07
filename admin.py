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
    @util.login_required
    def get(self):
        q = db.GqlQuery("SELECT * FROM Assassin")
        results = q.fetch(100)
        path = os.path.join(os.path.dirname(__file__), 'templates/admin.html')
        self.response.out.write(template.render(path, dict(assassins=results)))

class ModifyHandler(webapp.RequestHandler):
    def post(self):
        q = db.GqlQuery("SELECT * FROM Assassin")
        results = q.fetch(100)
        for assassin in results:
            id = assassin.id
            is_alive = bool(self.request.get(id + "_alive"))
            assassin.alive = is_alive

            target_id = self.request.get(id + "_target")
            q = db.GqlQuery("SELECT * FROM Assassin WHERE id= :1", target_id)
            results = q.fetch(1)
            target = results[0]

            assassin.target = target.user
            assassin.put()

        self.redirect("/admin/")

def main():
    template.register_template_library('filters')
    routes = [('/admin/', DefaultHandler),
              ('/admin/x', ModifyHandler)]

    application = webapp.WSGIApplication(routes,
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
