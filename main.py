#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import hashlib
import logging
import os
import urllib
import urlparse

from google.appengine.api import users, taskqueue
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util, template

from models import *
from util import *
 
class GuessMyKillerHandler(webapp.RequestHandler):
    @util.login_required
    def get(self):
        me = users.get_current_user()
        assassin = get_assassin_for_userid(me.user_id())
        if not assassin.alive:
            logging.warn("Assassin tried to guess their killer after they were killed")
            return

        q = db.GqlQuery("SELECT * FROM Assassin WHERE alive = :1", True)
        results = q.fetch(100)

        path = os.path.join(os.path.dirname(__file__), 'guess.html')
        self.response.out.write(template.render(path, dict(assassins=results)))
        
class DefaultHandler(webapp.RequestHandler):
    @util.login_required
    def get(self):
        me = users.get_current_user()
        logging.warn("UserID is %s" % me.email())
        q = db.GqlQuery("SELECT * FROM Assassin WHERE id = :1", me.user_id())
        results = q.fetch(1)
        logging.warn("I found %d people on main page" % len(results))
        logout_url = users.create_logout_url("/")
        if results:
            #user already exists, just say you've already signed up
            path = os.path.join(os.path.dirname(__file__), 'existing.html')
            self.response.out.write(template.render(path, dict(logout_url=logout_url)))

        else:
            path = os.path.join(os.path.dirname(__file__), 'signup.html')
            self.response.out.write(template.render(path, dict(logout_url=logout_url, 
                                                               name=me.nickname())))

class CreateHandler(webapp.RequestHandler):
#    @util.login_required
    def post(self):
        me = users.get_current_user()
        q = db.GqlQuery("SELECT * FROM Assassin WHERE id = :1", me.user_id())
        results = q.fetch(1)
        if not results: #avoid adding duplicate rows to the DB
            location = self.request.get("location")
            assassin = Assassin(location=location, id=me.user_id())
            assassin.put()

        qrcode_url = get_gchart_url(me.user_id(), self.request.url)
        path = os.path.join(os.path.dirname(__file__), 'create.html')
        self.response.out.write(template.render(path, dict(name=me.nickname(), qrcode_url=qrcode_url)))

class MainHandler(webapp.RequestHandler):
    @util.login_required
    def get(self, userid, digest):
        if not verify_digest(userid, digest):
            self.error(403)
            return

        me = users.get_current_user()
        if me.user_id() == userid:
            #yourself, just go ahead and say something kitschy
            path = os.path.join(os.path.dirname(__file__), 'init.html')
            self.response.out.write(template.render(path, dict(user=me)))
        else:
            #me just killed userid.  Enqueue a task item so we can notify them
            #find your Assassin object
            q = db.GqlQuery("SELECT * FROM Assassin WHERE id = :1", me.user_id())
            results = q.fetch(1)
            assassin = results[0]

            if not assassin.alive:
                logging.warn("A dead guy tried to play :(")
                return

            #ensure that you've hit the right person
            if assassin.target.user_id() != userid:
                path = os.path.join(os.path.dirname(__file__), 'wrong.html')
                args = dict(name=me.nickname(), target_name=assassin.user.nickname())
                self.response.out.write(template.render(path, args))
                return

            #find the other person userinfo
            q = db.GqlQuery("SELECT * FROM Assassin WHERE id = :1", userid)
            results = q.fetch(1)
            if len(results) != 1:
                logging.warn("No such user found ... how did that happen?")
            else:
                target=results[0]
                path = os.path.join(os.path.dirname(__file__), 'kill.html')
                args = dict(name=me.nickname(), target_name=target.user.nickname())
                self.response.out.write(template.render(path, args))

                num_alive = num_alive_assassins()
                if num_alive> 5:#give them a chance to save themselves
                    queue = Queue()
                    task = Task(method="POST", countdown=60, url="/tasks/notify",
                                params=dict(assassin=me.user_id(),
                                            target=target.id))
                    queue.add(task)
                else: #instant kill
                    assassin.kill(target)

class GenerateQRCode(webapp.RequestHandler):
    @util.login_required
    def get(self):
        user = users.get_current_user()
        userid = user.user_id()

        qrcode_url = get_gchart_url(userid, self.request.url)
        self.redirect(qrcode_url)

    def post(self):
        user = users.get_current_user()
        assassin_id = self.request.get("assassin")
        assassin = get_assassin_for_userid(assassin_id)
        if assassin.target == user.userid():
            #huzzah, the user guessed their assassin
            path = os.path.join(os.path.dirname(__file__), 'guess.html')
            self.response.out.write(template.render(path, dict(assassins=results)))

def main():
    routes = [('/user/(.*)/(.*)', MainHandler),
              ('/create', CreateHandler),
              ('/qrcode', GenerateQRCode),
              ('/guess', GuessMyKillerHandler),
              ('/', DefaultHandler)]

    application = webapp.WSGIApplication(routes,
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
