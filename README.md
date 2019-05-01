# gcodeEditor
A simple GUI gcode editor.

Uses gcode reader code from [zhangyaqi1989's Gcode-Reader](https://github.com/zhangyaqi1989/Gcode-Reader)

## Dependencies
This is being developed in python 3.7.3 and has not been tested with other iterations.

Packages:

- numpy 1.16.2
- pandas 0.24.2
- PyQt4 4.11.4
- pyqtgraph 0.10.0

## Usage
Launch the app with `python main.py` in the `/src/` directory.

Click on the "Open Gcode" button to load a .gcode file.

Use the spinner or the slider to change the displayed layer.

## TODOs
- Add 3D view of the paths, with layer display choice.
- Add path editing function in the 2D view.
