class Constraint {
    constructor() {
        if (new.target === Tool) {
            throw new TypeError("Cannot construct Abstract instances directly");
        }
    }

    cell_click(selector) {

    }

    cell_drag_enter(selector) {

    }

    numkey_press(num) {

    }
}