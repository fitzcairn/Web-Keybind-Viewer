'''
Routines for decoding input strings.
'''

import logging
import string

from layout       import Keyboards
from actionfilter import ActionFilterEncodeList
from base_convert import decode
from appengine    import get_versioned_memcache, put_versioned_memcache, get_ds


# The "id not found" icon/name pair.
_NOT_FOUND = ("INV_Misc_QuestionMark", "?")


# Supported mouse buttons.
# CMD -> Text shown
MOUSE_BUTTONS = {
    "MOUSEWHEELUP": "U",
    "MOUSEWHEELDOWN": "D",
    "BUTTON1":  "1",
    "BUTTON2":  "2",
    "BUTTON3":  "3",
    "BUTTON4":  "4",
    "BUTTON5":  "5",
    "BUTTON6":  "6",
    "BUTTON7":  "7",
    "BUTTON8":  "8",
    "BUTTON9":  "9",
    "BUTTON10": "10",
    "BUTTON11": "11",
    "BUTTON12": "12",
    "BUTTON13": "13",
    "BUTTON14": "14",
    "BUTTON15": "15",
    "BUTTON16": "16",
    "BUTTON17": "17",
}

# List for encoding, not exported
_MOUSE_BUTTONS = [
    "MOUSEWHEELUP",
    "MOUSEWHEELDOWN",
    "BUTTON1",
    "BUTTON2",
    "BUTTON3",
    "BUTTON4",
    "BUTTON5",
    "BUTTON6",
    "BUTTON7",
    "BUTTON8",
    "BUTTON9",
    "BUTTON10",
    "BUTTON11",
    "BUTTON12",
    "BUTTON13",
    "BUTTON14",
    "BUTTON15",
    "BUTTON16",
    "BUTTON17",
]


# Assume following code points for language layouts:
# 01 = Us-En
# 02 = DE
# ...
LANG_CODES = [
    None,
    'US-En',
    'DE',
]


# Assume following codes for mod key combinations
# 1: no mod keys
# 2: ctrl
# 3: alt
# 4: shift
# 5: ctrl + alt
# 6: ctrl + shift
# 7: ctrl + alt + shift 
# 8: alt  + shift
MOD_CODES = {
    '1': [],
    '2': ['CTRL'],
    '3': ['ALT'],
    '4': ['SHIFT'],
    '5': ['CTRL', 'ALT'],
    '6': ['CTRL', 'SHIFT'],
    '7': ['CTRL', 'ALT', 'SHIFT'],
    '8': ['ALT', 'SHIFT'],
}


# Bind type codes
# 0: [A]ction
# 1: [S]pell
# 2: [I]tem
# 3: [M]acro
# 4: [E]quipmentset
# ...?
TYPE_CODES = {
    '0': 'A',
    '1': 'S',
    '2': 'I',
    '3': 'M',
    '4': 'E',
}


# Bind source codes
# 1: [B]  (Blizzard)
# 2: [D]  (Dominos)
# 3: [BT] (Bartender)
# 4: [BP] (BindPad)
# 5: [P]  (Pet)
# 6: [S]  (Stance)
SRC_CODES = {
    '1': 'B',
    '2': 'D',
    '3': 'BT',
    '4': 'BP',
    '5': 'P',
    '6': 'S',
}


# Possible mods, for efficiency in later loops.  Not exported.
_MODS = { 'CTRL':1, 'ALT':1, 'SHIFT':1 }


# Build the decoding map from the keyboard layout.
# Returns a dict:
#
# {
#   lang: {
#           CODE: KEY_CMD
#           ...
#         }
# }
#
# Note: will throw an exception.
def build_decode_map():
    decode_map = {}
    
    for lang in Keyboards.keys():
        decode_map[lang] = {}
        i = 0
        for row in Keyboards[lang]['layout']:
            for k in row:
                cmd = k[0]
                if len(cmd) > 0 and not cmd.startswith("_") and cmd not in _MODS:
                    decode_map[lang][i] = cmd
                    i = i + 1
        # Add in mouse buttons.
        for cmd in _MOUSE_BUTTONS:
            decode_map[lang][i] = cmd
            i = i + 1
        
    return decode_map

# Create a decoded map ONCE, on load, grabbing from versioned memcached if poss.
KEY_CODES = get_versioned_memcache("key_codes")
if not KEY_CODES:
    KEY_CODES = build_decode_map()
    put_versioned_memcache("key_codes", KEY_CODES)


# Decode an API call string into a dict of binds from input.
# Rough EBNF of input format: [] = repeated, # = comment, etc
#
# input              = side num_mouse_buttons lang keys
# side               = digit
# num_mouse_buttons  = digit digit
# lang               = digit digit
# keys               = [key_code num_mod_blocks encoded_mod_vector]
# key_code           = digit digit digit
# num_mod_blocks     = digit
# encoded_mod_vector = [ length encoded_mod_block ] # len = num_mod_blocks
# encoded_mod_block  = encode(source mod_keys type id)
# source             = digit                        # From the source map
# type               = digit                        # From the types map
# id                 = [ digit ]                    # can be 1-5 digits long
# length             = digit
# digit              = 0-9
#
# Returns: side, buttons, lang, decoded_map
#
# side: Int, which side the mouse is on, 0 = left, 1 = right
# buttons: Int, number of mouse buttons
# lang: Str, decoded from LANG_CODES
# decoded_map: {
#                KEY:  [  # Str, decoded from KEY_CODES
#                        {
#                          m:  [...MOD STRS...], # List, decoded from MOD_CODES
#                          t:  <CODE>,           # Str, decoded from TYPE_CODES
#                          id: <ID>,             # Str, either spell, item, or icon ID
#                          ic: icon,             # Str, icon name
#                          s:  bind_src,         # Str, decoded from SRC_CODES
#                          n:  name,             # Str, spell/item name (or def for m/eqs)
#                         },
#                         ...
#                      ]
#                ...
#              }
#
# Note #1: we assume all characters are in ASCII range, (since the input
# string is url-safe) and do not bother to transcode to unicode.
#
# Note #2: Can throw exceptions.
def decode_api_call(url_input_string=''):
    input_vec   = list(url_input_string)
    lang        = ''
    b_icon      = None
    b_mods      = None
    b_type      = None
    b_id        = None
    b_src       = None
    b_name      = None
    t           = None
    decoded_map = {}
    buttons     = 2  # Default
    side        = 1  # Default right

    # Define a helper function that will pop n elements off the input
    # vector (def: input_vec defined above), and attempt to return
    # them concat'd as type t (def: int).
    def pop(n, t=int):
        ret, input_vec[:n] = input_vec[:n], []
        return t(''.join(ret))

    # Helper to pop a variable-length encoded value off
    # the input_str, decode it, and return it as an integer.
    def pop_encoded():
        v_len = pop(1)
        return decode(pop(v_len, str))

    # Helper to check if we're empty of all input
    def empty(): return len(input_vec) == 0

    # Make sure we have input
    if empty(): return (side, buttons, lang, decoded_map)

    # First digit is mouse side: required
    side = pop(1)

    # Second two digits are language code: required
    buttons = pop(2)

    # Third two digits are language code: required
    lang = LANG_CODES[pop(2)]

    # Ok to be empty after this point, means no keybinds at all.
    if empty(): return side, buttons, lang, decoded_map

    # Loop through binds until we're either empty or throw an
    # exception.  See EBNF above for overall flow explanation.
    while(not empty()):
        key_code       = pop(3)
        num_mod_blocks = pop(1)

        # Create map entry
        key = KEY_CODES[lang][key_code]
        decoded_map[key] = []
        
        # Iterate over the mod blocks and save into the map.
        for i in xrange(num_mod_blocks):
            encoded_mod_block = str(pop_encoded())
            b_src  = SRC_CODES[encoded_mod_block[0]]
            b_mods = MOD_CODES[encoded_mod_block[1]]
            b_type = TYPE_CODES[encoded_mod_block[2]]
            b_id   = encoded_mod_block[3:]

            # Actions don't have an icon, but need their name
            # decoded from ActionFilterEncodeList.
            if b_type == "A":
                b_icon = ""
                if b_id in ActionFilterEncodeList:
                    b_name = ActionFilterEncodeList[b_id]
                else:
                    b_name = "Unkown Action"

            # Decode icon
            else:
                # Note that M/E type have had their icons decoded
                # (matched to a spell id) in the lua, so this works
                # the same for them.
                if b_type == "M" or b_type == "E":
                    b_name, b_icon = get_ds(b_id, "S")
                else:
                    b_name, b_icon = get_ds(b_id, b_type)

                logging.info("ID: " + str(b_id) + " TYPE: " + str(b_type))

                # Did we miss?
                if not b_icon or not b_name:
                    b_icon, b_name = _NOT_FOUND

                # Macros and EQSs get static names
                if b_type == "M": b_name = "Macro"
                if b_type == "E": b_name = "Equipment Set"
                
            # Insert into map
            decoded_map[key].append({ 'm':  b_mods, 
                                      't':  b_type,
                                      's':  b_src,
                                      'n':  b_name,
                                      'ic': b_icon, 
                                      'id': b_id   })
    return side, buttons, lang, decoded_map


