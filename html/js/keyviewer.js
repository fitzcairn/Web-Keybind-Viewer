// Keyviewer-specific javascript functions.

// Main entry point for showing keyviewer hovers.  Takes in a CMD
// string and a JSON object with all information needed to do the
// rendering.
function show_hover(div, cmd, obj) {
    keybind_lib.show_key_hover(div, cmd, obj) 
}

// Control over interpretation library.  Uses hover library to power
// errors, etc.
var keybind_lib = {
    // Constructor
    init: function(div_list) {
        hover_class = 'key-hover';
        hover_id    = 'key-hover';

        // URL used to find images
        keybind_lib.img_src = "http://static.mmo-champion.com/db/img/icons/";

        // Code -> String table
        keybind_lib.src_map = {
            "B":  "Blizzard UI",
            "D":  "Dominos",
            "BT": "Bartender",
            "BP": "BindPad",
            "P":  "Pet Bar",
            "S":  "Stance Bar",
        };

        // Color control
        keybind_lib.colors = {
            "mod_on":     "#009999",
            "mod_off":    "#282d2f",
            "over":       "#993000",
            "has_bind":   "#993366",
        }

        // Create a timer ref
        keybind_lib.timer = null;

        // Create hover object.
        keybind_lib.hover        = win_lib.get_hover_lib(hover_id,
                                                         hover_class);
        keybind_lib.hover_div    = keybind_lib.hover.get_hover_ref();

        // Add a mouseout handler to the hover so that it gets hidden
        // when the user mouses out of it.  Also clear the timer.
        // Got some help here from http://www.quirksmode.org
        keybind_lib.hover_div.onmouseout  = function(e) { 
            var targ;
            if (!e) var e = window.event;
            if (e.target) targ = e.target;
            else if (e.srcElement) targ = e.srcElement;
            if (targ.nodeType == 3) // defeat Safari bug
                targ = targ.parentNode;
            
            // Handle event bubbling
            if (targ == keybind_lib.hover_div) {
                keybind_lib.hide_key_hover(keybind_lib.current_div, keybind_lib.current);
                if (keybind_lib.timer != null) clearTimeout(keybind_lib.timer);
            }
            else {
                e.cancelBubble = true;
                if (e.stopPropagation) e.stopPropagation();
            }
        }

        // Add a mouseover so that when the user enters the hover,
        // we don't hide the hover from them.
        keybind_lib.hover_div.onmouseover = function(evt) {
            if (keybind_lib.timer != null) clearTimeout(keybind_lib.timer);
        }

        // Go through the divs holding the keybinds, and color the
        // keys with binds.
        var element;
        var divs;
        for(var i = 0; i < div_list.length; i++) {
            element = document.getElementById(div_list[i]);
            if (element) {
                divs = element.getElementsByTagName("div");
                if (divs) {
                    for(var j = 0; j < divs.length; j++) {
                        // If the div has a mouseover, it has a bind.
                        if (divs[j].onmouseover != null) {
                            divs[j].style.backgroundColor = keybind_lib.colors.has_bind;
                        }
                    }
                }        
            }
        }          
    },


    // Helper function to get a list of the mod divs, by class ID.
    get_mod_div_list: function(mod_list) {
        var mod_divs = new Array();
        var key_list = document.getElementsByTagName('div');
        for(var i = 0; i < key_list.length; i++) {
            for(var j = 0; j < mod_list.length; j++) {
                if (key_list[i].className == mod_list[j]) {
                    mod_divs.push(key_list[i]);
                }
            }
        }
        return mod_divs;
    },
    

    // Construct the hover html from the bind object.
    // Note: returns HTML, not DOM objs!
    construct_hover_html: function(bind_obj) {
        var ret_html  = "<table class='tt_table'>";
        var bind_html = "";
        var s         = keybind_lib;
        var mod_str   = "";
        var seen      = new Array();
        var seen_key  = "";

        // Iterate through the bind object and construct the
        // html for each bind.
        for(var i = 0; i < bind_obj.length; i++) {
            if (bind_obj[i].id) {
                // TEMP: for now, reduce across bind id + type + mod strings.
                // This is until we can add bar/bind into the URL.
                // Avoid us looking stupid.
                seen_key = bind_obj[i].id + bind_obj[i].t + bind_obj[i].m.join("");
                if (seen[seen_key]) { }
                else {
                    seen[seen_key] = true;

                    // Only insert an image if this is a non-action type
                    if (bind_obj[i].t == "A") {
                        bind_html = "<tr><td></td><td>"
                            }
                    else {
                        bind_html = "<tr><td><a href='#' rel='spell=" + bind_obj[i].id +
                                    "'><img width='35' height='35' src='" +
                                    s.img_src + bind_obj[i].ic + ".png'></a></td><td>";
                    }

                    // Links for wowhead tooltips, again for non-action types
                    if      (bind_obj[i].t == "S")
                        bind_html += "<a href='#' rel='spell=" + bind_obj[i].id + "'>" + bind_obj[i].n + "</a> ";
                    else if (bind_obj[i].t == "I")
                        bind_html += "<a href='#' rel='item="  + bind_obj[i].id + "'>" + bind_obj[i].n + "</a> ";
                    else if (bind_obj[i].t == "A")
                        bind_html += bind_obj[i].n;
                    else
                        bind_html += "<a href='#'>";

                    // Mod keys to activate the bind
                    if (bind_obj[i].m[0]) {
                        mod_str = bind_obj[i].m.join(" ] + [ ");
                        bind_html += " with [ " + mod_str + " ] ";
                    }
                
                    // Source and done.
                    bind_html += " (" + s.src_map[bind_obj[i].s] + ")";
                    ret_html += bind_html + "</td></tr>";
                }
            }
        }
        return ret_html + "</table>";
    },


    // Highlight the mod keys for a given keybind.
    highlight_mods: function(bind_obj, on) {
        var s = keybind_lib;
        var mod_divs  = null;

        // Iterate through the bind object and highlight mods.
        for(var i = 0; i < bind_obj.length; i++) {
            if (bind_obj[i].id) {
                // Keys to activate the bind
                mod_divs = s.get_mod_div_list(bind_obj[i].m);
                if (mod_divs) {
                    for(var j = 0; j < mod_divs.length; j++) {
                        if (on) mod_divs[j].style.backgroundColor = s.colors.mod_on;
                        else    mod_divs[j].style.backgroundColor = s.colors.mod_off;
                    }
                }
            }   
        }
    },


    // Show the hover, registering it for a mouse-out hide.
    show_key_hover: function(key_div, cmd, bind_obj) {
        var control_obj = keybind_lib;

        // If there's a hover currently open, kill it first.
        if (keybind_lib.current) {
            keybind_lib.hide_key_hover(keybind_lib.current_div, keybind_lib.current);
            if (keybind_lib.timer != null) clearTimeout(keybind_lib.timer);
        }

        // Save the currently "on" info
        keybind_lib.current       = bind_obj;
        keybind_lib.current_div   = key_div;
        keybind_lib.current_color = key_div.style.backgroundColor;

        // Turn on mouseover highlight
        //key_div.style.backgroundColor = keybind_lib.colors.over;

        // Clear the timer; we're now showing a new hover.
        if (keybind_lib.timer != null) clearTimeout(keybind_lib.timer);

        // Get the div position and set it in the window object.
        pos = get_el_pos(key_div);

        // TODO: Is this the right position to anchor from?
        // MODIFY THIS
        keybind_lib.hover.set_anchor_pos(pos);

        // Construct the HTML to display
        var html = keybind_lib.construct_hover_html(bind_obj);

        // Highlight the mod keys that are used with this bind 
        keybind_lib.highlight_mods(bind_obj, true);

        // Add a timer to the calling div such that if the user
        // mouses out and does NOT enter the hover, the hover
        // dissappears.  We'll give them 1/2 sec (500ms)
        key_div.onmouseout = function(evt) {
            //keybind_lib.hide_key_hover(keybind_lib.current_div, keybind_lib.current)
            keybind_lib.timer = setTimeout(control_obj.timer_callback, 500);
        }

        // Render hover, 10 px offset from pos
        keybind_lib.hover.render_hover(html, -10);
    },


    // Helper to hide hover and reset state.
    hide_key_hover: function(key_div, bind_obj) {
        keybind_lib.hover.hide();
        keybind_lib.highlight_mods(keybind_lib.current, false);

        // Turn off mouseover
        //key_div.style.backgroundColor = keybind_lib.current_color;

    },

    // Timer callback
    // If the user hasn't entered the hover by n secs, then
    // turn off the hover.
    timer_callback: function () {
        keybind_lib.hide_key_hover(keybind_lib.current_div, keybind_lib.current);
    },
};

