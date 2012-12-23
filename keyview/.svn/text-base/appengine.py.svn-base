'''
Datastore-related methods.
'''

import logging
import random
import os


# Are we in unit-test mode?
# Only difference is that in unit-test mode we don't hit the daemon.
_UNIT_TEST = False

# Current app version
_CURR_VERSION = "1.0"

# We don't have access to appengine in the unit test scenario.  Turn on
# flag in that case.
try:
  from google.appengine.api import memcache
  from google.appengine.ext import db
  _CURR_VERSION = str(os.environ['CURRENT_VERSION_ID'])
except:
  _UNIT_TEST = True
  pass


#
# Memcached
#

# Get/put from memcached.  Implemented here to handle unit tests.
def get_memcache(key):
  if _UNIT_TEST: return None
  return memcache.get(key)
# Default ttl is 5 min.
def put_memcache(key, val, ttl=300):
  if _UNIT_TEST:  return True
  if val == None: return False
  return memcache.set(key, val, ttl)


# Get/put a memcached key that is localized to app version.
# Use case: updated keymapping modules should require a reload.
# Note: assumes key is a string.
def get_versioned_memcache(key):
  return get_memcache(_CURR_VERSION + key)
# Default ttl is 12 hours.
def put_versioned_memcache(key, val, ttl=259200):
  return put_memcache(_CURR_VERSION + key, val, ttl)


#
# Datastore
#

# Class to store ids -> names, icons
class WOWData(db.Model):
    ''' Wrapper around a bigtable class for Items.
    Local to this module only. '''
    name = db.StringProperty(required=True)
    icon = db.StringProperty(required=True)
    id   = db.StringProperty(required=True)


# Fetch functions; given id, return (name, icon)
# id is a string.
def get_ds(id, t):
    if _UNIT_TEST: return "testname", "testicon"
    key = t + id
    data = get_memcache(key)
    if not data: data = WOWData.get_by_key_name(key)
    if not data: return (None, None)
    put_memcache(key, data)
    return (data.name, data.icon)

