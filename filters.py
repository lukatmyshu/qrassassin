from google.appengine.ext import webapp

from util import *
register = webapp.template.create_template_register()

@register.filter
def make_user_url(userid):
    digest = make_digest(userid)
    return "/user/%s/%s" % (userid, digest)
