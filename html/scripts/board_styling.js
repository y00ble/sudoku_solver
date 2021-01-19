var BOX_BORDER_WIDTH = 3

var COLOR_MAP = {
    1: [93, 222, 108],
    2: [82, 210, 222],
    3: [145, 63, 204],
    4: [219, 61, 211],
    5: [209, 52, 60],
    6: [224, 153, 38],
    7: [225, 227, 82],
    8: [0, 0, 0],
    9: [148, 148, 148],
    0: [255, 255, 255],
}

var SELECTED_COLOR = [253, 255, 160]
var SELECTION_ALPHA = 0.6

function removeFromArray(arr) {
    var what, a = arguments, L = a.length, ax;
    while (L > 1 && arr.length) {
        what = a[--L];
        while ((ax = arr.indexOf(what)) !== -1) {
            arr.splice(ax, 1);
        }
    }
    return arr;
}

class Cell {
    static cornerClassOrder = [
        "top_left_corner",
        "top_corner",
        "top_right_corner",
        "left_corner",
        "right_corner",
        "bottom_left_corner",
        "bottom_corner",
        "bottom_right_corner",
        "weird_corner"
    ]

    constructor(row, column) {
        this.row = row;
        this.column = column;

        this.possibles = [];
        this.corner_marks = [];
        this.definite = null;
        this.selector = $(`.cell[row="${row}"][column="${column}"]`)
        this.color = COLOR_MAP[0];

        if (row == 1) {
            this.definite = 1;
        } else if (row == 2) {
            this.possibles = [2, 3, 4]
        } else if (row == 3) {
            this.corner_marks = [2, 3, 4]
        } else if (row == 4) {
            this.possibles = [2, 3, 4];
            this.corner_marks = [2, 3, 4];
        }
    }

    style_string() {
        var clauses = []
        if (this.row % 3 == 1) {
            clauses.push("border-top-width: " + BOX_BORDER_WIDTH.toString() + "px")
        }
        if (this.row % 3 == 0) {
            clauses.push("border-bottom-width:" + BOX_BORDER_WIDTH.toString() + "px")
        }
        if (this.column % 3 == 1) {
            clauses.push("border-left-width:" + BOX_BORDER_WIDTH.toString() + "px")
        }
        if (this.column % 3 == 0) {
            clauses.push("border-right-width:" + BOX_BORDER_WIDTH.toString() + "px")
        }

        if (this.row % 9 == 1) {
            clauses.push("border-top-width:" + 2 * BOX_BORDER_WIDTH.toString() + "px")
        }
        if (this.row % 9 == 0) {
            clauses.push("border-bottom-width:" + 2 * BOX_BORDER_WIDTH.toString() + "px")
        }
        if (this.column % 9 == 1) {
            clauses.push("border-left-width:" + 2 * BOX_BORDER_WIDTH.toString() + "px")
        }
        if (this.column % 9 == 0) {
            clauses.push("border-right-width:" + 2 * BOX_BORDER_WIDTH.toString() + "px")
        }

        clauses.push(`background-color: rgb(${this.get_color().join(",")})`);
        return clauses.join(";")
    }

    get_color() {
        if (this.selected()) {
            return [
                SELECTED_COLOR[0] * SELECTION_ALPHA + this.color[0] * (1 - SELECTION_ALPHA),
                SELECTED_COLOR[1] * SELECTION_ALPHA + this.color[1] * (1 - SELECTION_ALPHA),
                SELECTED_COLOR[2] * SELECTION_ALPHA + this.color[2] * (1 - SELECTION_ALPHA),
            ]
        } else {
            return this.color
        }
    }

    selected() {
        return $(`.cell[row=${this.row}][column=${this.column}]`).hasClass("selected")
    }

    html() {
        if (this.definite !== null) {
            return `<div class="mark_wrapper"><div class="cell_mark definite">${this.definite}</div></div>`
        }
        var corner_div = "";
        if (this.corner_marks.length != 0) {
            this.corner_marks.sort();
            for (var i = 0; i < this.corner_marks.length; i++) {
                corner_div += `<div class="corner_pencil ${Cell.cornerClassOrder[i]}">${this.corner_marks[i]}</div>`
            }
        }
        return `<div class="mark_wrapper"><div class="cell_mark centre_pencil">${this.possibles.join('')}</div>${corner_div}</div>`
    }

    process_digit(digit, tool) {
        if (tool === "corner") {
            if (this.corner_marks.includes(digit)) {
                removeFromArray(this.corner_marks, digit);
            } else {
                this.corner_marks.push(digit);
            }
        } else if (tool === "center") {
            if (this.possibles.includes(digit)) {
                removeFromArray(this.possibles, digit);
            } else {
                this.possibles.push(digit);
            }
        } else if (tool === "color") {
            this.color = COLOR_MAP[digit];
        } else {
            this.definite = digit;
        }
    }

}

var cells = [];

$(document).ready(function () {
    for (var row = 1; row <= 9; row++) {
        var row_cells = [];
        $(".grid").append(`<div class="row" row="${row}"></div>`)
        for (var column = 1; column <= 9; column++) {
            var cell = new Cell(row, column);
            $(`.row[row=${row}]`).append(`<div class="cell" row=${row} column=${column} style="${cell.style_string()}">${cell.html()}</div>`)
            row_cells.push(cell);
        }
        cells.push(row_cells);
    }

    $(".number_control").each(function (index) {
        var digit = parseInt($(this).html());
        $(this).mousedown(function () {
            add_digit_to_selection(digit);
        })

        $(this).append(`<div class="color_swatch" style="background-color: rgb(${COLOR_MAP[digit].join(",")});"></div>`)
    })

    $(".definite_button.mode_button").mousedown(function () { set_current_tool("definite") });
    $(".center_button.mode_button").mousedown(function () { set_current_tool("center") });
    $(".corner_button.mode_button").mousedown(function () { set_current_tool("corner") });
    $(".color_button.mode_button").mousedown(function () { set_current_tool("color") });
})