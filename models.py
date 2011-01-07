from google.appengine.ext import webapp, db
from google.appengine.api import mail

class Assassin(db.Model):
    def kill(self, victim):
        victim.alive = False
        victim.put()

        self.target = victim.target
        self.put()
        self.notify_assignment()

    def notify_assignment(self):
        args = dict(target = self.target.nickname(), nickname =self.user.nickname())
        mail.send_mail(sender="Assassins R Us <noone@example.com>",
                       to=self.user.email(),
                       subject="Your assignment",
                       body="""Dear %(nickname)s,
Go kill %(target)s""" % args)

    id = db.StringProperty(required=True)
    user = db.UserProperty(auto_current_user_add=True)
    location = db.StringProperty(required=True)
    alive = db.BooleanProperty()
    target = db.UserProperty()
        
class Kill(db.Model):
    user = db.UserProperty(auto_current_user_add=True)
    target = db.StringProperty()
    target_start_date = db.DateTimeProperty(auto_now_add=True)
    target_kill_date = db.DateTimeProperty()

class Assignment(db.Model):
    user = db.UserProperty()
    target = db.StringProperty()
