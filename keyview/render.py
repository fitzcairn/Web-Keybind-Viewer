'''
Rendering routines for keyboards.
'''

import cgi
import logging

from django.utils import simplejson as json

from layout    import Keyboards
from appengine import get_versioned_memcache, put_versioned_memcache
from encoding  import MOUSE_BUTTONS
from util      import float_to_str


# JS Constants
_ROLLOVER_JS       = 'OnMouseOver=\'show_hover(this, %s, %s);\''


# Create div html for keyboard objects.
# Data structure returned:
# {
#    html:  str   # HTML markup, with placeholders
#    val:   str,  # Value string
#    css:   list, # List of CSS commands
#    js:    list, # [], will be filled later.
#    cmd:   str   # cmd this div is for.
# }
def create_div_obj(cmd, val, w, h, x, y):
    css = []
    def style(p): # Convienience function.
        return css.append(p)
    
    # Dimensions
    style("height: " + float_to_str(h) + "%;")
    style("width:  " + float_to_str(w) + "%;")

    # Positioning
    style("left: " + float_to_str(x) + "%;")
    style("top: "  + float_to_str(y) + "%;")

    # Create and return structure
    return { 'html':  "<div class='%s' style='%s' %s>%s</div>",
             'val':   val,
             'css':   css,
             'js':    [],
             'cmd':   json.dumps(cmd),
            }


# Reset a div object to the original display state.
def reset_div_obj(obj):
    # Reset JS
    obj['js']    = []


# Given a key structure defined by create_div_obj, render it
# into an HTML string.
def render_div_obj(obj):
    return obj['html'] % (obj['cmd'],
                          ' '.join(obj['css']),
                          ' '.join(obj['js']),
                          obj['val'])
                     

# Build Keyboard HTML map.
# Creates a map of lang -> keyboard HTML, which can then be used to render
# the API parameters.
#
# Data structure returned:
# {
#   lang -> {
#             keys: {
#                     # Note: can have a multiple keys give the same CMD, like CTRL.
#                     CMD: [ { see create_div_obj() }, ... ]
#                     ...
#                   },
#             render_list: [ ... refs to key objects above in render order ... ]
#           },
#   ...
# }
def create_keyboard_html():
    board_html = {}
    pad_w      = 0
    pad_h      = 0
    key_w      = 0
    key_h      = 0
    row_h      = 0
    curr_x     = 0
    curr_y     = 0
    key_map    = None
    keyboard   = None
    
    # Board is layed out in percentages of input absolute dimensions.
    # Local helpers to do lookups.
    def _get_pct(tab, k):
        if k == None or k not in tab: return tab["_default"]
        return tab[k]
    def _get_w(board, k = None, w = None):
        return w or _get_pct(board['default_widths'], k)
    def _get_h(board, k = None, h = None):
        return h or _get_pct(board['default_heights'], k)

    # Loop through the board layout and construct the keys.
    for lang,board in Keyboards.items():
        board_html[lang] = {
            'keys':        {},
            'render_list': []
        }

        # Reset defaults
        pad_w   = _get_w(board, "_")
        pad_h   = _get_h(board, "_")
        row_h   = _get_h(board)
        key_w   = 0
        key_h   = 0
        curr_x  = 0
        curr_y  = 0
        key_map  = board_html[lang]['keys']
        keyboard = board_html[lang]['render_list']

        # Render board for this language.
        for row in board['layout']:
            rendered_row = []

            # Update width for new row.
            curr_x  = pad_w
        
            for key_tuple in row:
                # Pad out with None in the case there are no overrides.
                cmd, key, key_w, key_h = (key_tuple + [None, None, None])[0:4]
                key_w = _get_w(board, cmd, key_w)
                key_h = _get_h(board, cmd, key_h)

                if key:
                    # Create, size, and position the key
                    k_obj = create_div_obj(cmd, key,
                                            key_w, key_h,
                                            curr_x, curr_y)

                    # Add to map
                    if cmd in key_map: key_map[cmd].append(k_obj)
                    else: key_map[cmd] = [k_obj]

                    # Add to render list.
                    keyboard.append(k_obj)

                # If there is no key, don't create a button, but still add space.
                curr_x = curr_x + key_w + pad_w
            
            # Update height for new row, accounting for empty rows.
            if len(row) > 0: curr_y = curr_y + row_h + pad_h
            else:            curr_y = curr_y + pad_h
    return board_html


# Build the Keyboard HTML, grabbing from versioned memcached if poss.
# See create_keyboard_html() for structure details.
KEYBOARD_HTML = get_versioned_memcache("key_html")
if not KEYBOARD_HTML:
    KEYBOARD_HTML = create_keyboard_html()
    put_versioned_memcache("key_html", KEYBOARD_HTML)


# Take in a parsed parameter set and create the keyboard HTML
# Returns a string of HTML.
# For the structure of decoded_map see the comments for decode_api_call()
def render_keyboard(lang, decoded_map={}):
    # Update the key state with the decoded binds.
    for cmd,obj in KEYBOARD_HTML[lang]['keys'].items():
        if cmd in decoded_map:
            # Highlight keys with binds, and add a JS callback
            # to show the rollover.
            for k in KEYBOARD_HTML[lang]['keys'][cmd]:
                k['js'] = [_ROLLOVER_JS % (json.dumps(cmd),
                                           json.dumps(decoded_map[cmd]))]
        else:
            # Reset appearance
            map(reset_div_obj, KEYBOARD_HTML[lang]['keys'][cmd])

    # Render keyboard for language.
    return ''.join(map(render_div_obj, KEYBOARD_HTML[lang]['render_list']))


# Create the mouse HTML.  Returns a string of HTML
# Note that here we can't pre-construct anything and memcache it,
# as the HTML depends heavily on num_buttons.  Create on-demand.
def render_mouse(buttons, decoded_map={}):
    # Helper for building the render list,
    render_list = []
    def add_div(cmd, key, key_w, key_h, x, y):
        return render_list.append(create_div_obj(cmd, key, key_w, key_h, x, y))

    # Assume 100% of the frame is available.
    w = 100
    h = 100

    # Spacer for display elements.
    m_s = 2

    # Set mouse body dims in terms of percentage.
    m_w = 60
    m_h = 70

    # Dimensions for display elements for the mouse.
    m_frame_h = m_h * 0.5
    m_frame_w = m_w
    m_b_rl_h  = m_h * 0.5 - m_s
    m_b_rl_w  = m_w * 0.40
    m_b_mi_h  = ((m_h * 0.5) / 3) - m_s
    m_b_mi_w  = m_w * 0.20 - (2 * m_s)
    
    # Create the mouse UI elements
    # Are there buttons to render outside of 1-3?  If so, make room.
    left = 0
    if buttons <= 3: left = 20
    off_x, off_y = (left, 0)

    # Button 1,2, and the frame
    add_div("BUTTON1",        "1", m_b_rl_w,  m_b_rl_h,  off_x, off_y) # Left button
    off_x = left + m_b_rl_w + m_b_mi_w + (m_s * 2)
    add_div("BUTTON2",        "2", m_b_rl_w,  m_b_rl_h,  off_x, off_y) # Right button
    off_x, off_y = (left, m_b_rl_h + m_s)
    add_div("FRAME",          " ", m_frame_w, m_frame_h, off_x, off_y) # Bottom of mouse
    
    # Up, 3, Down
    off_x, off_y = (left + m_b_rl_w + m_s, 0)
    add_div("MOUSEWHEELUP",   "U", m_b_mi_w,  m_b_mi_h, off_x, off_y) # Mouseup
    off_y = off_y + m_b_mi_h + m_s
    add_div("BUTTON3",        "3", m_b_mi_w,  m_b_mi_h, off_x, off_y) # Middle button
    off_y = off_y + m_b_mi_h + m_s
    add_div("MOUSEWHEELDOWN", "D", m_b_mi_w,  m_b_mi_h, off_x, off_y) # Mousedown

    # Create any extras buttons on the side required.
    if buttons > 3:
        # Dimensions for buttons 3+ along the side
        button_w = w - m_w - m_s
        button_h = (h - ((buttons - 3 - 1) * m_s)) / (buttons - 3)

        # Sanity check for looks.
        if button_h > (0.4 * button_w): button_h = (0.4 * button_w)

        # Create buttons
        off_x = m_w + m_s
        off_y = 0
        i = 4
        while (i <= buttons):
            add_div("BUTTON" + str(i), str(i), button_w, button_h, off_x, off_y)
            off_y = off_y + button_h + m_s
            i     = i + 1
    
    # TODO: use decoded_map to update CSS/JS
    # Highlight keys with binds.
    for obj in render_list:
        cmd = obj['cmd']
        if cmd in decoded_map:
            obj['js'] = [_ROLLOVER_JS % (json.dumps(cmd),
                                         json.dumps(decoded_map[cmd]))]
        else:
            # Reset appearance
            reset_div_obj(obj)
            
    # Render and return mouse html.
    return ''.join(map(render_div_obj, render_list))


# Render the board and mouse html, returning mouse, keyboard
# TODO: EXPLAIN PARAMS
# Note: can throw exceptions.
def render_html(buttons=3, lang='US-En', decoded_map={}):
    # Get the mouse and keyboard html
    mouse_html    = render_mouse(buttons, decoded_map)
    keyboard_html = render_keyboard(lang, decoded_map)

    return mouse_html, keyboard_html


# Render an error string.
def render_noinput_error():
    return """Welcome to Fitzcairn's Keybind Viewer!
    <br><br>
    This site is still under heavy testing and is in early Beta.  To see how it will be used, please see <a href='/about#how'>'How to Use this Site'</a>.
    <br><br>
    In the meantime, here are some demo links from low-level test characters.  These were generated automatically via the soon-to-be-released update to <a href="http://wow.curse.com/downloads/wow-addons/details/keybindviewer.aspx">
    KeybindViewer</a>:
    <br><br>
    <a href="http://kbv.fitztools.com/v10501017152K0aR013132z503312gK09714CRNy016152J.LO057132z3037132y.015152K0av059132yV031132yU090132yV018152J.PA058132z603812gL091132z9098132z900322lj32yS082132y.02314CRNy087132za00222lm32yX022243Wmf4CRNy040132zc036132yZ021132Bl035232za33IZ00122le32z2089132z603212gP004233ej32y_088132z302024CRNy3pKK064151Gp7S00012gM045137an">Example 1</a> (Hunter), 
    <a href="http://kbv.fitztools.com/v1050101723pHy3pHy013132z5036132yZ073132z001633pxm32Bo32Bo057132z3037132y.015543Wmf3pxm43Wmf43Wmf3pBd059132yV031132yU090132yV018232Bo3pBd058132z603812gL091132z9098132z9019243Wij43Wij00322lj32yS082132y.087132za00232lm53ieZK32yX02214JG4R025143Wmf06012gO089132z6040132zc00132le32z253icA803312gK035232za33IZ06112gR004233ej32y_02014CYtD03212gP00012gM088132z3">Example 2</a> (Warrior), 
    <a href="http://kbv.fitztools.com/v00701013132z503312gK073132z0057132z3037132y.01513pGe059132yV031132yU090132yV058132z603812gL091132z9098132z900322lj32yS082132y.023143Vae087132za00222lm32yX02213pys02514CIZD06012gO040132zc02113pB6036132yZ00122le32z2035232za33IZ089132z6004233ej32y_03212gP02013ufi088132z300012gM06112gR">Example 3</a> (Warlock, Left-handed, 7 button mouse)
    <br><br> 
    Thanks, and check back soon!
    """




# Render an error string.
def render_parse_error():
    return "I couldn't parse the URL into keybinds.  Please ensure the address is correct."


# Render an error string.
def render_render_error():
    return "An error occurred in rendering.  The problem has been logged and will be investigated ASAP."

