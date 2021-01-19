var current_tool = "definite"
var temp_tool = null;
var controlling = 0;
var shifting = 0;
var alting = 0;


function get_current_tool() {
    if (temp_tool != null) {
        return temp_tool;
    } else {
        return current_tool;
    }

}

function refresh_tool_frontend() {
    var tool = get_current_tool();

    $(".number_control").removeClass("corner_button").removeClass("center_button")
    $(".mode_button").removeClass("selected_mode_button")
    $(".color_swatch").css("display", "none")

    if (tool == "corner") {
        $(".mode_button.corner_button").addClass("selected_mode_button")
        $(".number_control").addClass("corner_button")
    } else if (tool == "center") {
        $(".mode_button.center_button").addClass("selected_mode_button")
        $(".number_control").addClass("center_button")
    } else if (tool == "definite") {
        $(".mode_button.definite_button").addClass("selected_mode_button")
    } else if (tool == "color") {
        $(".mode_button.color_button").addClass("selected_mode_button")
        $(".color_swatch").css("display", "block")
    }
}


function set_temp_tool(name) {
    temp_tool = name;
    refresh_tool_frontend()
}

function set_current_tool(name) {
    current_tool = name;
    set_temp_tool(null);
}

function get_current_pivot() {
    var row = parseInt($(".pivot").attr('row'));
    var column = parseInt($(".pivot").attr('column'));
    return [row, column]
}


function add_digit_to_selection(digit) {
    var tool = get_current_tool();
    $(".selected").each(function (index) {
        var row = $(this).attr("row");
        var column = $(this).attr("column");
        cell = cells[row - 1][column - 1];
        cell.process_digit(digit, tool);
    })
}


function refresh_board() {
    $(".cell").each(function (index) {
        var row = $(this).attr("row");
        var column = $(this).attr("column");
        cell = cells[row - 1][column - 1];
        $(this).html(cell.html());
        $(this).attr("style", cell.style_string());
    })
}


function select(selector, incremental) {
    $(".cell").removeClass("pivot");
    if (!incremental) {
        $(".cell").removeClass("selected");
    }
    selector.addClass("selected").addClass("pivot");
}

function rotClamp(num, min, max) {
    if (num < min) {
        return rotClamp(max - (min - num) + 1, min, max)
    }
    if (num > max) {
        return rotClamp(num - max, min, max)
    }
    return num
}

var left_mouse = false;
var right_mouse = false;
var middle_mouse = false;

$(document).ready(function () {
    $(".cell").on("dragstart mousedown", function (event) {
        select($(this), (event.ctrlKey || event.shiftKey))
    })

    $(".cell").mouseenter(function (event) {
        if (left_mouse) {
            select($(this), true)
        }
    })

    $(".cell").on('dragenter', function (event) {
        select($(this), true)
    })

    $(document).mousedown(function (event) {
        switch (event.which) {
            case 1:
                left_mouse = true;
                break;
            case 2:
                middle_mouse = true;
                break;
            case 3:
                right_mouse = true;
                break;
        }
        refresh_board()
    });

    $(document).mouseup(function (event) {
        switch (event.which) {
            case 1:
                left_mouse = false;
                break;
            case 2:
                middle_mouse = false;
                break;
            case 3:
                right_mouse = false;
                break;
        }
        refresh_board()
    });

    $(document).keyup(function (event) {
        var keycode = (event.keyCode ? event.keyCode : event.which);
        if (keycode == '17') {
            set_temp_tool("center");
            event.preventDefault();
            controlling -= 1;
            if (controlling === 0) {
                if (shifting === 0) {
                    if (alting === 0) {
                        set_temp_tool(null);
                    } else {
                        set_temp_tool("color")
                    }
                } else {
                    set_temp_tool("corner")
                }
            }
        } else if (keycode == '16') {
            event.preventDefault();
            shifting -= 1;
            if (shifting === 0) {
                if (controlling === 0) {
                    if (alting === 0) {
                        set_temp_tool(null);
                    } else {
                        set_temp_tool("color")
                    }
                } else {
                    set_temp_tool("center")
                }
            }
        } else if (keycode == '18') {
            event.preventDefault();
            alting -= 1;
            if (alting === 0) {
                if (controlling === 0) {
                    if (shifting === 0) {
                        set_temp_tool(null);
                    } else {
                        set_temp_tool("corner")
                    }
                } else {
                    set_temp_tool("center")
                }
            }
        }
        alting = Math.max(alting, 0)
        shifting = Math.max(shifting, 0)
        controlling = Math.max(shifting, 0)
        refresh_board()
    })

    $(document).keydown(function (event) {
        var keycode = parseInt(event.keyCode ? event.keyCode : event.which);
        var pivot = get_current_pivot()
        var pivot_changed = false;
        if (keycode == 38) {
            pivot[0] -= 1;
            event.preventDefault();
            pivot_changed = true;
        } else if (keycode == 40) {
            pivot[0] += 1;
            event.preventDefault();
            pivot_changed = true;
        } else if (keycode == 37) {
            pivot[1] -= 1;
            event.preventDefault();
            pivot_changed = true;
        } else if (keycode == 39) {
            pivot[1] += 1;
            event.preventDefault();
            pivot_changed = true;
        } else if (keycode == 17) {
            set_temp_tool("center");
            event.preventDefault();
            controlling += 1;
        } else if (keycode == 16) {
            set_temp_tool("corner");
            event.preventDefault();
            shifting += 1;
        } else if (keycode == 18) {
            set_temp_tool("color");
            event.preventDefault();
            alting += 1;
        } else if ((48 <= keycode) && (keycode <= 57)) {
            var digit = keycode - 48;
            add_digit_to_selection(digit);
            event.preventDefault();
        } else if ((96 <= keycode) && (keycode <= 105)) {
            var digit = keycode - 96;
            add_digit_to_selection(digit);
            event.preventDefault();
        } else if (keycode == 90) {
            set_current_tool("definite");
            event.preventDefault();
        } else if (keycode == 88) {
            set_current_tool("center");
            event.preventDefault();
        } else if (keycode == 67) {
            set_current_tool("corner");
            event.preventDefault();
        } else if (keycode == 86) {
            set_current_tool("color");
            event.preventDefault();
        }
        pivot[0] = rotClamp(pivot[0], 1, 9)
        pivot[1] = rotClamp(pivot[1], 1, 9)
        if (pivot_changed) {
            selector = $(`div[row=${pivot[0]}][column=${pivot[1]}]`)
            select(selector, (event.ctrlKey || event.shiftKey))
        }
        refresh_board()
    })
})