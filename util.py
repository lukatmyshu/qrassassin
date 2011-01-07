import hashlib
import logging
import urllib
import urlparse

from google.appengine.ext import db

SECRET = "breakfastofchampions"

def get_assassin_for_userid(userid):
    q = db.GqlQuery("SELECT * FROM Assassin WHERE id = :1", userid)
    results = q.fetch(1)
    return results[0]

def verify_digest(userid, digest):
    expected_digest = hashlib.sha1(userid + SECRET).hexdigest()
    return expected_digest == digest

def make_digest(userid):
    return hashlib.sha1(userid + SECRET).hexdigest()

def get_gchart_url(userid, url):
    digest = make_digest(userid)
    baseurl="https://chart.googleapis.com/chart?cht=qr&chs=400&chl=%s"

    parts = urlparse.urlparse(url)._replace(path="/user/%s/%s" % (userid, digest))
    newurl = urlparse.urlunparse(parts)

    logging.warn("URL is %s" % newurl)
    return baseurl % urllib.quote(newurl)

def num_alive_assassins():
    q = db.GqlQuery("SELECT * FROM Assassin WHERE alive=:1", True)
    results = q.fetch(100)

    return len(results)
