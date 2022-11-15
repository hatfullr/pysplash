import sys
if sys.version_info.major < 3:
    import Tkinter as tk
else:
    import tkinter as tk

from lib.widgetcontroller import WidgetController

class GUIWidgetController:
    def __init__(self, gui):
        self.gui = gui
        self._widgetcontrollers = []
        self.controls()
        self.plot_controls()

    def _add(self, *args, **kwargs):
        self._widgetcontrollers.append(WidgetController(*args, **kwargs))

    def controls(self):
        # Comboboxes
        for axis_controller in [self.gui.controls.axis_controllers['XAxis'], self.gui.controls.axis_controllers['YAxis']]:
            self._add(
                axis_controller.combobox,
                self.gui.has_data,
                self.gui.data_is_image,
                comparison = [
                    True,
                    False,
                ],
                true = {'state' : 'normal'},
                false = {'state' : 'disabled'},
                default = {'state' : 'disabled'},
            )
        self._add(
            self.gui.controls.axis_controllers['Colorbar'].combobox,
            self.gui.has_data,
            self.gui.data_is_image,
            self.gui.controls.axis_controllers['XAxis'].value,
            self.gui.controls.axis_controllers['YAxis'].value,
            comparison=[
                True,
                False,
                ['x','y','z'],
                ['x','y','z'],
            ],
            true = {'state' : 'normal'},
            false = {'state' : 'disabled'},
            default = {'state' : 'disabled'},
        )
            
        # Scales
        for axis_controller in self.gui.controls.axis_controllers.values():
            self._add(
                axis_controller.scale.linear_button,
                axis_controller.value,
                comparison = [
                    ["", " ", None, "None", "none"],
                ],
                true = {'state' : 'disabled'},
                false = {'state' : '!disabled'},
            )

            self._add(
                axis_controller.scale.log_button,
                axis_controller.scale.log_allowed,
                true = {'state' : '!disabled'},
                false = {'state' : 'disabled'},
            )

            self._add(
                axis_controller.scale.pow10_button,
                axis_controller.scale.pow10_allowed,
                true = {'state' : '!disabled'},
                false = {'state' : 'disabled'},
            )

        # Limits
        for axis_controller in self.gui.controls.axis_controllers.values():
            self._add(
                axis_controller.limits.adaptive_button,
                self.gui.has_data,
                true = {'state' : '!disabled'},
                false = {'state' : 'disabled'},
            )
            self._add(
                axis_controller.limits.entry_low,
                axis_controller.limits.adaptive,
                true = {'state' : 'disabled'},
                false = {'state' : '!disabled'},
            )
            self._add(
                axis_controller.limits.entry_high,
                axis_controller.limits.adaptive,
                true = {'state' : 'disabled'},
                false = {'state' : '!disabled'},
            )





        

    def plot_controls(self):
        widgets = [
            self.gui.controls.plotcontrols.rotation_x_entry,
            self.gui.controls.plotcontrols.rotation_y_entry,
            self.gui.controls.plotcontrols.rotation_z_entry,
        ]
        for widget in widgets:
            self._add(
                widget,
                self.gui.has_data,
                self.gui.data_is_image,
                self.gui.time_mode,
                self.gui.controls.axis_controllers['XAxis'].value,
                self.gui.controls.axis_controllers['YAxis'].value,
                comparison = [
                    True,
                    False,
                    False,
                    ['x','y','z'],
                    ['x','y','z'],
                ],
                true = {'state' : 'normal'},
                false = {'state' : 'disabled'},
                default = {'state' : 'disabled'},
            )
        self._add(
            self.gui.controls.plotcontrols.point_size_entry,
            self.gui.interactiveplot.plot_type,
            comparison = ['ScatterPlot', 'PointDensityPlot'],
            true = {'state' : 'normal'},
            false = {'state' : 'disabled'},
        )
