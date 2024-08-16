'''This file contains the Options_Window class.

Contains the Options_Window class, which defines a Toplevel window that grabs the focus from the main window 
defined in GUI_prototype_10.py. The Options_Window class uses a list of widget dictionaries corresponding to the 
element added by the Gui class to display the relevant widgets for choosing the element's settings. This is done in
the display_elements method. Multipoles and RF cavities require more than 1 options window, and these are handled in
their own methods. The beam options window is controlled by the beam_options method. Note that the confirm buttons
for these windows aren't defined in the Options_Window class, and rather by the Gui class, as they are bound to Gui
methods.
'''

#import modules
import tkinter as tk
import sys
import numpy as np
import GUI_dicts

#define constants
MIN_FLOAT = sys.float_info.min
MAX_FLOAT = sys.float_info.max

#define dictionary of widgets for setting up beam
BEAM_SETUP = GUI_dicts.BEAM_SETUP

class Options_Window(tk.Toplevel):
	'''Class creating a window that pops up and prompts user to input values for the settings needed
	'''
	def __init__(self):
		'''Creates a new window as a tkinter TopLevel object and grabs focus
		'''
		super().__init__()
		self.focus()
		self.grab_set()
		
	def display_options(self, choice, radius):
		'''Displays the widgets for choosing the settings of whichever element has been selected
		
		For the element chosen in the GUI code, the correct widgets are selected from the ALL_OPTIONS dictionary which 
		uses the element name as a key. The list of widget dictionaries is then iterated through and each one displayed 
		in the window. 
		
		----arguments----
			choice: str
				name of the element selected by user in GUI code
			radius: float
				radius of ring. Used to calculate bounds on element settings
		
		---variables/attributes defined inside---
			max_angle: float
				maximum angle a component can occupy (from centre of ring). Used in ALL_OPTIONS
			ALL_OPTIONS: dict
				dictionary containing the list of widgets for each element. Structure is 
				{"name of element":[{"widget": tkinter widget object, "options"{dict of widget arguments},...}],...}
			options_dict: list
				list of widget dictionaries corresponding to the element chosen
			scale_list: list
				list of every widget requiring a user input
			widget_list: list
				list of all widgets displayed as part of setting selection
			widget_type: str
				Class name of widget (not instantiated)
			options: dict
				dictionary of widget arguments
			widget: tkinter object
				instantiated tkinter widget
		'''
		self.choice = choice
		self.radius = radius
		max_angle = round(np.pi, 2)
		
		ALL_OPTIONS = GUI_dicts.make_all_options(max_angle, self.radius)
		self.options_dict = ALL_OPTIONS[choice]
		
		self.scale_list = []
		self.widget_list = []
		for i in range(0, len(self.options_dict)):
			widget_type = self.options_dict[i]["widget"]
			options = self.options_dict[i]["options"]
			widget = widget_type(self, **options)
			widget.pack()
			self.widget_list.append(widget)
			if widget_type == tk.Scale or widget_type == tk.Entry:
				self.scale_list.append(widget)
	
	def multipole_more_options(self, chosen_settings):
		'''Lets user select the field strength of each order in multipole
		
		Destroys previous widgets from selecting the length and number of orders, then creates a number of entry widgets 
		equal to the number of orders chosen. scale_list is reset and filled with the entry widgets created. Sliders and 
		labels are added to the screen. 
		
		----arguments----
			chosen_settings: list
				list containing the settings chosen from the initial multipole options screen. Structure 
				is [length, number of orders]
		
		---variables/attributes defined inside---
			order: int
				number of orders/entry widgets
			label: tkinter Label object
				label widget containing text depending on the order the slider below it is for		
		'''
		for i in self.widget_list:
			i.destroy()
		order = int(chosen_settings[3])
		self.scale_list = []
		for i in range(0, order):
			label = tk.Label(self, text = "order: " + str(i) + " (-2 to 2 T)")
			self.scale_list.append(tk.Entry(self))
			label.pack()
			self.scale_list[i].pack()
	
	def rf_more_options(self):
		'''Lets user choose dimensions of RF cavity after choosing the time dependence parameters
		
		Destroys previous widgets, and re-runs display_options with "RF more" as the element name. 
		'''
		for i in self.widget_list:
			i.destroy()
		self.display_options("RF more", self.radius) 
		
	def beam_options(self, particle_choice):
		'''Lets user choose beam/distribution settings
		
		Runs instead of choose_options if chosen in GUI code. Uses BEAM_SETUP, which is a list of widget dicionaries 
		used for choosing beam settings. Iterates through this list and displays widgets in the same way as
		choose_options, using input_list instead of scale_list and beam_widget_list instead of widget_list. Also 
		creates an option menu for choosing the particle type
		
		----arguments----
			particle_choice: tkinter StringVar object
				contains particle currently displayed in particle choice menu
						
		---variables/attributes defined inside---
			input_list: list
				list of all widgets prompting a user input
			beam_widget_list: list
				list of all widgets used to choose beam settings
		'''
		self.input_list = []
		self.beam_widget_list = []
		for i in range(0, len(BEAM_SETUP)):
			widget_type = BEAM_SETUP[i]["widget"]
			options = BEAM_SETUP[i]["options"]
			widget = widget_type(self, **options)
			widget.grid()
			self.beam_widget_list.append(widget)
			if widget_type == tk.Scale or widget_type == tk.Entry:
				self.input_list.append(widget)
			
		self.particle_choice = particle_choice
		self.particle_menu = tk.OptionMenu(self, self.particle_choice, "proton", "electron", "muon")
		self.particle_menu.grid()
		
