# gcodeEditor
A simple GUI gcode editor.

Uses gcode reader code from [zhangyaqi1989's Gcode-Reader](https://github.com/zhangyaqi1989/Gcode-Reader)

## Dependencies
This is being developed in python 3.7.1 and has not been tested with other iterations.

Packages:

- numpy 1.16.3
- pandas 0.24.2
- PyQt 5.9.7
- pyqtgraph 0.10.0
- pyopengl 3.1.1a1

## Usage
Launch the app with `python main.py` in the `/src/` directory.

Click on the "Open Gcode" button to load a .gcode file.

In the Single Layer View, use the spinner or the slider to change the displayed layer.

In the 3D view, use the range slider or the spinners to change the range of displayed layers.

## TODOs
- Add path editing function in the 2D view.
