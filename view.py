#
# Handle views
#

import os
import cgi
import logging

from google.appengine.api             import users
from google.appengine.ext             import webapp
from google.appengine.ext.webapp      import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext             import db

from keyview.render   import render_html, render_noinput_error, render_parse_error, render_render_error
from keyview.encoding import decode_api_call


# Save the template path from this CGI
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__),
                             'templates')


# EXAMPLE INPUT:
# v1030105734CLdh51hZ5V41gXA
# v1030105814CH5O
# (see encoding.txt)

class MainPage(webapp.RequestHandler):
  def get(self):
    side, buttons, lang, decoded_map = (1, 2, "US-En", {})
    template_vals = { 'content': '', 'error_box': '' }
    
    # Get the call param, everything after /v
    param = self.request.path[2:]

    # SPECIAL CASE: no input!  Show directions page.
    if len(param) == 0:
      template_vals["error_box"] = template.render(os.path.join(_TEMPLATE_PATH,
                                                                'error.template'),
                                                   { 'error': render_noinput_error() })
    # Attempt to decode it.
    else:
      try:
        side, buttons, lang, decoded_map = decode_api_call(param)
      except Exception, inst:
        logging.error(param)
        logging.error(str(inst))
        template_vals["error_box"] = template.render(os.path.join(_TEMPLATE_PATH,
                                                                  'error.template'),
                                                     { 'error': render_parse_error() })

    # Rendering the keyboard and mouse display.
    try:
      mouse, keyboard = render_html(buttons, lang, decoded_map)
    except Exception, inst:
        logging.error(param)
        logging.error(decoded_map)
        logging.error(str(inst))
        template_vals["error_box"] = template.render(os.path.join(_TEMPLATE_PATH,
                                                                  'error.template'),
                                                     { 'error': render_render_error() })
 
    # Fill in values
    content_vals = { 'mouse': mouse, 'keyboard': keyboard }
    if side == 1: # Mouse on right
      template_vals['content'] = template.render(os.path.join(_TEMPLATE_PATH,
                                                              'right.template'),
                                                 content_vals)
    else:
      template_vals['content'] = template.render(os.path.join(_TEMPLATE_PATH,
                                                              'left.template'),
                                                 content_vals)

    # Render out
    self.response.out.write(template.render(os.path.join(_TEMPLATE_PATH,
                                                         'base.template'),
                                            template_vals))


# Handle about pages
class AboutPage(webapp.RequestHandler):
  '''
  Handles displaying about page.
  '''

  # Simple fetch
  def get(self):
    '''
    Display About page.
    '''
    about = template.render(os.path.join(_TEMPLATE_PATH,
                                         "about.template"),
                            {});
    self.response.out.write(template.render(os.path.join(_TEMPLATE_PATH,
                                                         'base.template'),
                                                          {'content': about}))


''' Register handlers for WSCGI. '''
application = webapp.WSGIApplication([('/about', AboutPage),
                                      ('/.*',   MainPage )],
                                     debug=False)
def real_main():
    run_wsgi_app(application)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    real_main()
