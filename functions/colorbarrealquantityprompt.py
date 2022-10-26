from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
    
import globals

from widgets.popupwindow import PopupWindow
from widgets.comboboxchoicecontrols import ComboboxChoiceControls
from lib.tkvariable import StringVar

class ColorbarRealQuantityPrompt(PopupWindow, object):
    def __init__(self, gui):
        if globals.debug > 1: print("colorbarrealquantityprompt.__init__")
        super(ColorbarRealQuantityPrompt, self).__init__(
            gui,
            title="Choose a quantity",
            oktext="Done",
            okcommand=self.ok_command,
            cancelcommand=self.close,
            name='colorbarrealquantityprompt',
        )

        self.gui = gui

        self.create_variables()
        self.create_widgets()
        self.place_widgets()
        
        self.okpressed = False


    def create_variables(self, *args, **kwargs):
        if globals.debug > 1: print("colorbarrealquantityprompt.create_variables")
        self.variable = StringVar(self, None, 'variable')
        
    def create_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("colorbarrealquantityprompt.create_widgets")
        self.description = ttk.Label(
            self.contents,
            text="Choose one of the options below to control how plots will be created. If you choose 'opacity' then the integration performed at each pixel of the plot will be attenuated by the particle opacity values, found as an SPH summation. If you choose 'tau' then whenever the quantity being integrated is calculated at a given position, each contribution to that sum will be attenuated by the contributing particle's tau value.",
            wraplength=self.width-2*self.cget('padx'),
            justify='left',
        )

        disabled_choices = []
        choices = ('opacity', 'tau')
        for choice in choices:
            if not self.gui.data.has_variables(choice): disabled_choices.append(choice)
        
        self.combobox = ComboboxChoiceControls(
            self.contents,
            textvariable=self.variable,
            values=choices,
            disabled=disabled_choices,
            state='readonly',
        )
        
    def place_widgets(self, *args, **kwargs):
        if globals.debug > 1: print("colorbarrealquantityprompt.place_widgets")

        self.description.pack(side='top',fill='both',expand=True)
        self.combobox.pack(side='top')
        
    def ok_command(self, *args, **kwargs):
        if globals.debug > 1: print("colorbarrealquantityprompt.ok_command")
        self.okpressed = True
        self.close()

    def close(self, *args, **kwargs):
        if globals.debug > 1: print("colorbarrealquantityprompt.close")
        if self.okpressed:
            self.gui.controls.colorbar_real_mode.set(self.variable.get())
            self.gui.controls.previous_colorbar_type = 'real'
        else:
            # Set the colorbar type back to whatever it was before the user
            # clicked "Real"
            widgets = [
                self.gui.controls.colorbar_integrated_button,
                self.gui.controls.colorbar_surface_button,
            ]
            for widget in widgets:
                if widget.value == self.gui.controls.previous_colorbar_type:
                    widget.invoke()
                    break
        super(ColorbarRealQuantityPrompt, self).close(*args,**kwargs)
