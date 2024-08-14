#import modules
import tkinter as tk
import multiprocessing as mp
import os
import sys
import math
import pyopal.elements.local_cartesian_offset
import pyopal.elements.scaling_ffa_magnet
import pyopal.elements.multipolet
import pyopal.elements.asymmetric_enge
import pyopal.elements.probe
import pyopal.objects.field
import pyopal.elements.polynomial_time_dependence
import pyopal.elements.variable_rf_cavity
import GUI_runner
import numpy as np
import opt_window
import GUI_dicts

MAX_FLOAT = sys.float_info.max
MIN_FLOAT = sys.float_info.min

#dictionary for colour of each element
COLOURS = GUI_dicts.COLOURS

#dictionary for widgets used to set up beam, their arguments, and bounds for validation of entries
BEAM_SETUP = GUI_dicts.BEAM_SETUP

class Gui():
	'''Class defining the GUI object
	
	Has all GUI widgets as attributes, as well as the runner being used, the 2 main windows, and several Boolean flags. 
	Takes OPAL_list, py_list and beam_list as args. These are lists in the shared memory space between parent and child processes.
	'''
	def __init__(self, OPAL_list, py_list, beam_list):
		'''Initiates the GUI object
		
		Sets the intial values of key counters and flags, then calls the make_interface method. 
		
		----arguments----
		OPAL_list
		py_list
		beam_list
		
		---variables/attributes defined inside---
			fork_number: int
				keeps track of number of times the parent process has forked (increments when OPAL executes)
			keep_window: Bool
				says whether the main window is being closed and restarted or not. Initialised as false so the 
				window gets setup in the first run.
			ring_flag: Bool
				says whether the ring is the only element being set up or not. If false, the ring and beam setups are
				run. If true, only the ring is set up. Initialised as false so both are set up in first run.
		'''
		self.fork_number = 0
		self.keep_window = False
		self.ring_flag = False
		self.make_interface(OPAL_list, py_list, beam_list)
	
	def make_interface(self, OPAL_list, py_list, beam_list):
		'''Make window and display widgets for first part of setup
		
		Makes main window and defines widgets for setting up the ring and beam, or just the ring if ring_flag is true. 
		
		----arguments----
		OPAL_list
		py_list
		beam_list
		
		---variables/attributes defined inside---
			root: 
				main window object from tkinter
			cart_photo: str
				gets the cartesian field map image from the correct file
			cyl_photo: str
				gets the cylindrical field map image from the correct file
			invalid_label: tkinter Label
				label showing the current error message (or lack thereof)
		'''
		if self.keep_window == False:
			self.root = tk.Tk()	
			self.end_button = tk.Button(self.root, text = "Finish Program", command = self.root.destroy)
			self.end_button.grid(row = 0, column = 0)
			self.invalid_label = tk.Label(self.root, text = "")
		
		#Find image files	
		self.cart_photo = tk.PhotoImage(file="scaling_ffa_map_cart.png")
		self.cyl_photo = tk.PhotoImage(file="scaling_ffa_map_cyl.png")
		
		self.r_label = tk.Label(self.root, text = "Radius of ring (above 0 [m])")
		self.r_label.grid(row = 1, column = 0)
		self.r_entry = tk.Entry(self.root)
		self.r_entry.grid(row = 2, column = 0)
		
		self.input_list = []
		self.ring_widget_list = []
		
		#Display widgets for creating beam if beam is being made/reset
		if self.ring_flag == False:
			self.ring_widget_list, self.input_list = display_widgets(self.root, BEAM_SETUP, self.ring_widget_list, self.input_list, 3, 0)
			
			#Sets up option menu for particle type
			self.particle_choice = tk.StringVar(self.root)
			self.particle_choice.set("proton")
			self.particle_menu = tk.OptionMenu(self.root, self.particle_choice, "proton", "electron", "muon")
			self.particle_menu.grid(row = 3 + len(BEAM_SETUP), column = 0)
				
		self.r_confirm = tk.Button(self.root, text = "Confirm settings", command = lambda: self.check_ring(OPAL_list, py_list, beam_list))
		self.r_confirm.grid(row = 4 + len(BEAM_SETUP), column = 0)
		self.invalid_label.grid(row = 5 + len(BEAM_SETUP), column = 0)
		
	def check_ring(self, OPAL_list, py_list, beam_list):
		'''Checks selected ring/beam options are valid
		
		Validates user inputs for the ring if ring_flag is True, or the beam AND ring if ring_flag is false. If valid, sets radius and 
		appends the beam settings to beam_list. If invalid, prompts user to try again.
		
		----arguments----
		OPAL_list
		py_list
		beam_list
		
		---variables/attributes defined inside---
			radius: float
				radius of ring (between 0 and 4 [m])
			beam_settings: list
				array containing the validated beam settings (gamma, x, px, y, py, z, pz)
			ring_widget_list: list
				array containing all widgets used in setting up the beam
		'''
		#validate radius input
		invalid_flag = False
		radius_check = self.r_entry.get()
		valid, message = validate_input(radius_check, MIN_FLOAT, MAX_FLOAT)
		
		if valid != None:
			self.radius = valid
		else:
			invalid_flag = True
			display_message = message
		
		#validate beam settings if they were set/reset
		if invalid_flag == False and self.ring_flag == False:
			beam_settings = []
			self.BOUNDS_DICT = GUI_dicts.define_bounds_dict(self.radius, 0)
			beam_settings, invalid_flag, display_message = validation_loop(self.input_list, self.BOUNDS_DICT["beam"], beam_settings)
			
		#destroy old widgets				
		if self.ring_flag == False:				
			remove_widgets(self.ring_widget_list)
				
		self.r_confirm.destroy()
		self.r_label.destroy()
		self.r_entry.destroy()
		
		if self.ring_flag == False:
			self.particle_menu.destroy()
		
		#restart initial menu if invalid	
		if invalid_flag == True:
			self.keep_window = True
			self.make_interface(OPAL_list, py_list, beam_list)
			self.invalid_label.config(text = display_message)
		else:
			if self.ring_flag == False:
				self.invalid_label.config(text = "")
				particle = self.particle_choice.get().upper()
				gamma = beam_settings[0]
				start_coords = [beam_settings[1], beam_settings[2], beam_settings[3], beam_settings[4], beam_settings[5], beam_settings[6]]
				self.set_beam(beam_list, particle, gamma, start_coords)
			else:
				self.set_beam(beam_list, beam_list[0], beam_list[1], beam_list[2])
				
			self.setup_ring(OPAL_list, py_list, beam_list)
	
	def setup_ring(self, OPAL_list, py_list, beam_list):
		'''Creates runner object, defines its attributes, gives option to make cell
		
		Instantiates the runner object from the class in GUI_runner.py. Sets the runner's r0 attribute to be the chosen radius, 
		defines the directory the plots go in, and its post-process. Also shows widgets giving the user the option to define a
		repeatable cell element, and sets some flags.
		
		----arguments----
		OPAL_list
		py_list
		beam_list
		
		---variables/attributes defined inside---
			runner: OPAL Runner object
				object from class in GUI_runner.py. Inherits from minimal_runner also.
			ring_space: float
				attribute tracking the amount of space left in the ring [m]
			full: Bool
				flag that says if ring is full or not
			made_cell: Bool
				flag that says whether a cell element has already been made or not
			making_cell:  Bool
				flag that says whether a cell is currently being made or not
			cell_widgets: Bool
				flag that says whether or not the widgets for making a cell are currently being displayed
		'''
		#instantiate minimal runner
		self.runner = GUI_runner.Runner(OPAL_list, py_list, beam_list)
		self.runner.bend_direction = 1
		self.runner.r0 = self.radius
		self.runner.plot_dir = os.getcwd()
		self.runner.postprocess = self.runner.plots

		
		#set flags and attributes
		self.ring_space = self.radius * 2 * np.pi
		self.full = False
		self.made_cell = False
		self.making_cell = False
		
		#gives user option to make cell
		self.make_cell_text = tk.Label(self.root, text = "Would you like to define a repeatable cell element?")
		self.make_cell_text.grid(row = 1)
		self.make_cell_button = tk.Button(self.root, text = "yes", command = lambda: self.make_cell(OPAL_list, py_list, beam_list))
		self.make_cell_button.grid(row = 2)
		self.continue_button = tk.Button(self.root, text = "no", command = lambda: self.design_ring(OPAL_list, py_list, beam_list))
		self.continue_button.grid(row = 3)
		self.cell_widgets = True
		
	def make_cell(self, OPAL_list, py_list, beam_list):
		'''Lets user make a repeatable cell element.
		
		Shows the widgets for adding elements to the cell and destroys the previous widgets. Changes the flags so other methods adapt
		for a cell being made instead of ring. Sets some attributes describing the cell.
		
		----arguments----
		OPAL_list
		py_list
		beam_list
		
		---variables/attributes defined inside---
		cell_length_list: list
			list containing the lengths of each element added to cell so the cell element can be deleted form the ring later on
		cell: list
			list containing every element in the cell and its settings
		cell_size: float
			stores the current length of the cell
		'''
		#destroy old widgets
		self.make_cell_text.destroy()
		self.make_cell_button.destroy()
		self.continue_button.destroy()
		self.cell_widgets = False
		
		#set cell attributes
		self.cell_length_list = []
		self.cell = []
		self.cell_size = 0
		self.making_cell = True
		
		#display widgets for making cell
		choice = tk.StringVar(self.root)
		choice.set("Scaling FFA magnet")
		self.info_label = tk.Label(self.root, text = "Add elements to cell:")
		self.info_label.grid(row = 1)
		self.menu = tk.OptionMenu(self.root, choice, "Scaling FFA magnet", "Drift", "Multipole", "RF Cavity")
		self.menu.grid(row = 2)
		
		self.cell_label = tk.Label(self.root, text = "")
		self.cell_label.grid(row = 3)
		self.cell_display = ""
		
		self.cell_confirm = tk.Button(self.root, text = "confirm cell", command = lambda: self.confirm_cell(OPAL_list, py_list, beam_list))
		self.cell_confirm.grid(row = 7)
		
		self.add_button = tk.Button(self.root, text = "Add element", command = lambda: self.add_element(choice, py_list))
		self.add_button.grid(row = 5)
		
		self.delete_button = tk.Button(self.root, text = "delete last element", command = lambda: self.delete_element(py_list))
		self.delete_button.grid(row = 6)
	
	def update_with_element(self, py_list, new_element, display_settings, length, add):
		display = ""
		display += new_element
		for key in display_settings:
			display += ", " + key + ": " + str(display_settings[key]) 
		display += "\n"
		
		if self.making_cell == True:
			self.cell_display += display
			self.cell_label.config(text = self.cell_display)
			self.cell_length_list.append(length)
			self.cell_size += length
			self.cell.append(add)
		else:
			self.element_display += display
			self.element_label.config(text = self.element_display)
			self.ring_space -= length
			self.space_label.config(text = "Ring space: " + str(self.ring_space))
			self.space_list.append(length)
			py_list.append(add)
			
		
	def confirm_cell(self, OPAL_list, py_list, beam_list):
		'''Saves the cell and moves to the ring building screen.
		
		Moves from the cell building screen to the ring building screen, setting flags and destroying cell making
		widgets.  
		----arguments----
		OPAL_list
		py_list
		beam_list
		'''
		#destroy old widgets
		self.cell_label.destroy()
		self.info_label.destroy()
		self.menu.destroy()
		self.cell_confirm.destroy()
		self.add_button.destroy()
		self.delete_button.destroy()
		
		#set flags
		self.making_cell = False
		self.made_cell = True
		
		#go to ring building screen
		self.design_ring(OPAL_list, py_list, beam_list)
		self.invalid_label.config(text = "")
		
	def design_ring(self, OPAL_list, py_list, beam_list):
		'''Displays widgets for building the ring
		
		Lets user add elements. Uses flags tp operate differently if a cell has been defined. If the cell has been defined, the
		cell creation widgets are destroyed, and the cell is listed as an option in the menu for adding elements. 
		
		----arguments----
		OPAL_list
		py_list
		beam_list
		
		---variables/attributes defined inside---
		space_list: list
			list of the lengths of each element added (like cell_length_list but for the full ring)
		'''
		#destroy old widgets if cell was made
		if self.cell_widgets == True:
			self.make_cell_text.destroy()
			self.make_cell_button.destroy()
			self.continue_button.destroy()
		
		#make widgets for ring creation
		self.space_list = []
		self.plot_button = tk.Button(self.root, text = "Run", command = lambda: self.fork(OPAL_list, py_list, beam_list))
		self.plot_button.grid(row = 0, column = 1)
		choice = tk.StringVar(self.root)
		choice.set("Scaling FFA magnet")
		self.info_label = tk.Label(self.root, text = "Add elements to build ring:")
		self.info_label.grid(row = 2, column = 0)
		
		#add cell as an option if it was defined
		if self.made_cell == True:
			self.menu = tk.OptionMenu(self.root, choice, "Scaling FFA magnet", "Drift", "Multipole", "RF Cavity", "Cell")
		else:
			self.menu = tk.OptionMenu(self.root, choice, "Scaling FFA magnet", "Drift", "Multipole", "RF Cavity")
			
		self.menu.grid(row = 3, column = 0)
		self.add_button = tk.Button(self.root, text = "Add element", command = lambda: self.add_element(choice, py_list))
		self.add_button.grid(row = 5, column = 0)
		self.element_label = tk.Label(self.root, text = "")
		self.element_label.grid(row = 4, column = 0)
		self.delete_button = tk.Button(self.root, text = "delete last element", command = lambda: self.delete_element(py_list))
		self.delete_button.grid(row = 6, column = 0)
		self.element_display = ""
		self.space_label = tk.Label(self.root, text = "Ring space: ")
		self.space_label.grid(row = 7, column = 0)
		
	def add_element(self, choice, py_list):
		'''Adds new element based on what the user selected and lets them choose its parameters
		
		Defines a dictionary of the bounds for each parameter of each possible element. If the ring is not full, the settings
		screen for the new element is displayed by defining the options_window object from the class in opt_window.py. If the 
		ring is full, the user is told to choose a different element or run OPAL. Cell element handled seperately as no 
		settings need to be chosen.
		
		----arguments----
		choice: tkinter StringVar object
			stores the value currently displayed in the element option menu
		py_list
		
		---variables/attributes defined inside---
		new_element: str
			stores the name of the new element being added
		BOUNDS_DICT: dict
			dictionary containing bounds for each setting of every element
		element_display: str
			string containing the contents of the ring and the settings of each element. Displayed in a label
		options_window:
			object from the class in opt_window.py. Opens a new window and shifts focus to it so main window can't be edited
			whilst it's open
		
		Note that for each element added, a dictionary is defined containing its settings and a list defined for appending to
		py_list. Their structures are as follows:
		
		settings = ["argument":value, ...]
		add = [{"element_type": pyOpal object, "length":length}, settings]
		'''
		#checks if ring is full
		if self.full:
			self.full_label.destroy()
			self.full = False
			
		new_element = choice.get()
		
		#defines bounds dictionary
		self.BOUNDS_DICT = GUI_dicts.define_bounds_dict(self.radius, self.ring_space)
		
		#seperate handling for cell element
		if new_element == "Cell":
			temp_space = self.ring_space
			temp_space -= self.cell_size
			if temp_space >= 0:
				self.element_display += "Cell \n"
				self.element_label.config(text = self.element_display)
				self.ring_space = temp_space
				self.space_list.append(self.cell_size)
				for i in range(0, len(self.cell)):
					py_list.append(self.cell[i])
			else:
				self.full_label = tk.Label(self.root, text = "Ring full. Add different element or execute")
				self.full_label.grid(row = 8, column = 0)
				self.full = True
				
			self.space_label.config(text = "Ring space: " + str(self.ring_space))
		
		#opens options window for other elements and adds confirm button to it
		else:
			self.options_window = opt_window.Options_Window()
			self.options_window.display_options(new_element, self.ring_space, self.radius)
			self.confirm = tk.Button(self.options_window, text = "confirm settings", command = lambda: self.get_choices(self.options_window.scale_list, new_element, py_list))
			self.confirm.pack()
	
	def get_choices(self, scale_list, new_element, py_list):
		'''Gets user inputs from option window and validates them.
		
		Uses the scale_list attribute from options_window, which contains a list of all widgets taking user input. Iterates through
		this list, getting the value from each input and validating it using the bounds. If any input invalid, the options screen is 
		destroyed and a message printed. If all inputs valid, options_window is destroyed and a function is called based on what 
		element has been chosen. 
		
		----arguments----
		scale_list: list
			list containing all the input widgets in the options window
		new_element: str
			name of element selected from menu
		py_list
		
		---variables/attributes defined inside---
		invalid_flag: Bool
			flag that says whether and invalid input has been encountered. Set to True if validation fails for any setting
		chosen_settings: list
			list containing the validated settings chosen for the element by the use
		scale_list: list
			list of all widgets used for input in options window
		setting: str	
			temporary variable storing the raw value obtained from the input widget
		bounds_list: list
			list containing the upper and lower bound of each setting
		lower_bound: float
			lower bound of setting
		upper_bound: float
			upper bound of setting
		valid: 
			value returned by validation function called on setting. None if invalid, and validated setting if valid
		'''
		self.chosen_settings = []
		self.chosen_settings, invalid_flag, display_message = validation_loop(scale_list, self.BOUNDS_DICT[new_element], self.chosen_settings)
		
		if invalid_flag == False:
			self.invalid_label.config(text = "")
			if new_element == "Scaling FFA magnet":
				self.options_window.destroy()
				self.add_ffa_mag(py_list)
			elif new_element == "Drift":
				self.options_window.destroy()
				self.add_drift(py_list)
			elif new_element == "Multipole":
				self.options_window.multipole_more_options(self.chosen_settings)
				self.confirm.configure(command = lambda: self.get_orders(py_list))
			elif new_element == "RF Cavity":
				self.options_window.rf_more_options()
				self.confirm.configure(command = lambda: self.get_rf_dimensions(py_list))
		else:
			self.options_window.destroy()
			self.invalid_label.config(text = display_message)
		
	def get_orders(self, py_list):
		'''Lets user choose the field strength of each pole in a multipole element
		
		Multipole handled differently in options_window. This uses the options_window attribute slider_list, which is a list of
		field strength entries needed based on the number of poles the user selected (displayed in the options window). This list
		is iterated through and the value got from each slider. These are validated in the same way as before. If invalid input
		encountered, the addition of the multipole is cancelled. If all inputs valid, they are appended to a list of field strengths
		and add_multipole is called.
		
		----arguments----
		py_list
		
		---variables/attributes defined inside---
		t_p: list
			list containing the field stength of each pole
		field: str
			temporary variable storing raw value from entry
		valid: 	
			as in get_choices
		'''
		t_p = []
		t_p, invalid_flag, display_message = validation_loop(self.options_window.scale_list, self.BOUNDS_DICT["Multipole more"], t_p)
		
		if invalid_flag == False:
			self.chosen_settings.append(t_p)
			self.options_window.destroy()
			self.invalid_label.config(text = "")
			self.add_multipole(py_list)
		else:
			self.options_window.destroy()
			self.invalid_label.config(text = display_message)
	
	def get_rf_dimensions(self, py_list):
		'''Lets user choose the dimensions of the RF cavity after time dependences have been set
		
		RF cavity handled differently in options_window. After time dependence set from initial options window, the window
		is updated with widgets for choosing the dimensions. This function uses scale_list from options_window as before to 
		get and validate the user input for dimensions. If no invalid values encountered, add_rf is called. If any value is 
		invalid, this screen is called again and a message printed.
		
		----arguments----
		py_list
		'''
		
		self.chosen_settings, invalid_flag, display_message = validation_loop(self.options_window.scale_list, self.BOUNDS_DICT["RF more"], self.chosen_settings)
		
		if invalid_flag == True:
			self.invalid_label.config(text = display_message)
			self.options_window.destroy()
		else:
			self.invalid_label.config(text = "")
			self.options_window.destroy()
			self.add_rf(py_list)
		
	def reset(self, OPAL_list, py_list, beam_list):
		'''Resets the entire program and starts again. 
		
		All initial attributes are reset, as well as the lists in shared memory. make_interface is then called.	
		'''
		py_list *= 0 
		OPAL_list *= 0
		self.fork_number = 0
		self.root.destroy()
		self.keep_window = False
		self.ring_flag = False
		self.make_interface(OPAL_list, py_list, beam_list)
	
	def reset_ring(self, OPAL_list, py_list, beam_list):
		'''Resets the ring 
		
		Clears py_list and OPAL_list in shared memory, and sets ring_flag to True so only the ring is set up when make_interface
		is called. 
		'''
		py_list *= 0
		OPAL_list *= 0
		self.ring_flag = True
		self.keep_window = False
		self.root.destroy()
		self.make_interface(OPAL_list, py_list, beam_list)
				
	def add_ffa_mag(self, py_list):
		'''Adds an FFA magnet to the ring/cell
		
		Sets parameters from user input and defines settings as a dictionary. If making a ring, and there is enough space,
		the magnet is added to the ring and its length subtracted from ring_space. The element and its settings are added
		to py_list. If making a cell, the magnet size is added to the cell size and the settings appended to the cell array.
		Either element_display or cell_display updated with the magnet and its settings. 
		
		----arguments----
		py_list
		
		---variables/attributes defined inside---
		b0: float
			b0 constant in expression for magnetic field [T]
		k_value: float
			field index
		f_start:
			distance from start of magnet at which field rises to half the peak value [m]
		f_centre_length: float
			length of the plateau of field strength [m]
		f_end: float
			distance from end of plateau to start of next element (determines how fast field drops off) [m]
		temp_space: float
			temporary variable used to check if ring is full (if adding to ring and not cell)
		'''
		#set chosen settings
		b0 = self.chosen_settings[0]
		k_value = self.chosen_settings[1]
		f_start = self.chosen_settings[2]
		f_end_length = self.chosen_settings[3]
		f_centre_length = self.chosen_settings[4]
		radial_neg_extent = self.chosen_settings[5]
		radial_pos_extent = self.chosen_settings[6]
		
		f_end = f_start + f_centre_length + f_end_length * 4
		temp_space = self.ring_space
		temp_space -= f_end
		
		#check if ring full
		if temp_space >= 0:
			#define settings and list appended to py_list or cell
			settings = {
				"b0":b0, 
				"r0":self.radius, 
				"field_index":k_value, 
				"tan_delta":math.tan(self.runner.spiral_angle), 
				"radial_neg_extent":radial_neg_extent, 
				"radial_pos_extent":radial_pos_extent,
				"azimuthal_extent":self.runner.cell_length, 
				"magnet_start":f_start, "end_length":f_end_length, 
				"centre_length":f_centre_length, 
				"magnet_end":f_end
				}
			
			add = [{"element_type":pyopal.elements.scaling_ffa_magnet.ScalingFFAMagnet}, settings]
			
			display_settings = {"b0": b0, "k":k_value, "start":f_start, "centre_length":f_centre_length, "end length":f_end_length}
			self.update_with_element(py_list, "Scaling FFA magnet", display_settings, f_end, add)
			
		#tell user ring is full
		else:
			self.full_label = tk.Label(self.root, text = "Ring full. Add different element or execute")
			self.full_label.grid(row = 8, column = 0)
			self.full = True
	 	
	def add_drift(self, py_list):
		'''Adds a drift space to the ring/cell
		
		Sets parameters from user input and defines settings and add. If the ring is being made and there is enough space,
		adds the drift to the ring and subtracts length (calculated from angle) from ring space. The element and its settings
		are added to py_list. If making a cell, the drift size is added to the cell size and the settings appended to the 
		cell array. Either element_display or cell_display updated with the magnet and its settings
		
		----arguments----
		py_list
		
		---variables/attributes defined inside---
		req_angle: float
			angle taken up by drift space (from centre of ring) [rad]
		'''
		req_angle = self.chosen_settings[0]
		
		settings = {
			"end_position_x" : self.runner.bend_direction * self.radius * (math.cos(req_angle) - 1), 
			"end_position_y" : self.radius * math.sin(req_angle), 
			"end_normal_x" : -self.runner.bend_direction * math.sin(req_angle), 
			"end_normal_y":math.cos(req_angle)
			}
		
		add = [{"element_type":pyopal.elements.local_cartesian_offset.LocalCartesianOffset}, settings]
		
		display_settings = {"angle": req_angle}
		length = self.radius * req_angle
		self.update_with_element(py_list, "Drift", display_settings, length, add)
		
	def add_multipole(self, py_list):
		'''Add a general multipole to ring/cell
		
		Sets list of field strengths and length from user input and defines settings and add. If the ring is being made,
		adds the drift to the ring and subtracts length from ring space. The element and its settings are added to py_list. 
		If making a cell, the length is added to the cell size and the settings appended to the cell array. Either
		element_display or cell_display updated with the magnet and its settings. Note that the bounds of length were defined 
		by ring_space, so no need to check if ring is full.
		
		----arguments----
		py_list
		
		---variables/attributes defined inside---
		length and t_p as before
		angle: float
			angle taken up by multipole (from centre of ring) [m]. Calculated from length
		'''

		length = self.chosen_settings[0]
		horizontal_aperture = self.chosen_settings[1]
		vertical_aperture = self.chosen_settings[2]
		t_p = self.chosen_settings[4]
		angle = np.arccos(1 - length ** 2 / (2 * self.radius ** 2))
		
		settings = {
			"t_p":t_p, 
			"angle":angle, 
			"length":length, 
			"maximum_f_order":5, 
			"horizontal_aperture":horizontal_aperture, 
			"vertical_aperture":vertical_aperture, 
			"left_fringe":0.01, 
			"right_fringe":0.01, 
			"entrance_angle":0.0, 
			"maximum_x_order":5, 
			"bounding_box_length":100
			}
		
		add = [{"element_type":pyopal.elements.multipolet.MultipoleT}, settings]
		
		display_settings = {"fields":t_p, "length": length}
		self.update_with_element(py_list, "Multipole", display_settings, length, add)

		self.confirm.destroy()
    
	def add_rf(self, py_list):
		'''Adds an RF cavity to ring/cell
		
		Sets time dependence coefficients for phase, amplitude and frequency from user input, as well as cavity dimensions. Defines
		settings and add, but these are later updated in OPAL code to include the time dependence objects (as defined objects can't 
		be in shared memory). If the ring is being made, adds the cavity to the ring and subtracts length from ring space. The element 
		and its settings are added to py_list.  If making a cell, the length is added to the cell size and the settings appended to the 
		cell array. Either element_display or cell_display updated with the magnet and its settings. Note that the bounds of length were 
		defined by ring_space, so no need to check if ring is full.
		
		----arguments----
		py_list
		
		---variables/attributes defined inside---
		for each of phase, amp and freq:
			p0: float
				p0 coefficient in polynomial time dependence
			p1: float
				p1 coefficient in polynomial time dependence
			p2: float
				p2 coefficient in polynomial time dependence
		'''
		#get settings from chosen_settings
		phase_p0 = self.chosen_settings[0]
		phase_p1 = self.chosen_settings[1]
		phase_p2 = self.chosen_settings[2]
		
		amp_p0 = self.chosen_settings[3]
		amp_p1 = self.chosen_settings[4]
		amp_p2 = self.chosen_settings[5]
		
		freq_p0 = self.chosen_settings[6]
		freq_p1 = self.chosen_settings[7]
		freq_p2 = self.chosen_settings[8]
		
		length = self.chosen_settings[9]
		width = self.chosen_settings[10]
		height = self.chosen_settings[11]
		
		settings = {
			"length":length, 
			"width":width, 
			"height":height, 
			"phase_p0":phase_p0, 
			"phase_p1":phase_p1, 
			"phase_p2":phase_p2, 
			"amp_p0":amp_p0, 
			"amp_p1":amp_p1, 
			"amp_p2":amp_p2, 
			"freq_p0":freq_p0, 
			"freq_p1":freq_p1, 
			"freq_p2":freq_p2
			}

		add = [{"element_type":pyopal.elements.variable_rf_cavity.VariableRFCavity}, settings]
		
		display_settings = {"length":length, "width": width, "height":height}
		self.update_with_element(py_list, "RF", display_settings, length, add)
        
	def delete_element(self, py_list):
		'''Delete last element in the cell/ring
		
		Deletes last element in the cell/ring by removing the last element from the cell or py_list. First, it is checked whether 
		the ring/cell is already empty or not, and a message returned if it is. The space is added/subtracted from the ring/cell 
		using space_list or cell_length_list as stacks and subtracting the last length. If the cell element is removed from the 
		ring, cell_length list is iterated through and each length subtracted from ring_space. The number of indices from py_list
		to be removed is calculated, and py_list updated. cell_display or element_display also updated.
		
		----arguments----
		py_list
		
		---variables/attributes defined inside---
		string: list
			list made from splitting cell_display or element_display at new line characters. Indices removed from string, 
			and the display reformed from the remaining elements.
		display_add: str
			each line of the display to be added to cell_display or element_display. Formed from iterating through string
		delete_indices: int
			number of indices to be removed from the ring if the cell element is deleted. Calculated from length of cell  
		'''
		#checks if cell or ring is being made
		if self.making_cell == True:
			#checks if cell is empty
			if len(self.cell) > 0:
				string = self.cell_display.split("\n")
				self.cell_display = ""
				string = string[:-2]
				self.cell = self.cell[:-1]
				for i in string:
					display_add = i + "\n"
					self.cell_display += display_add
				self.cell_label.config(text = self.cell_display)
				self.cell_size -= self.cell_length_list[-1]
				self.cell_length_list = self.cell_length_list[:-1]
			else:
				print("Already empty")
		else:
			#checks if ring is empty
			if len(py_list) > 0:
				string = self.element_display.split("\n")
				self.element_display = ""
				
				#handles cell element differently
				if string[-2] == "Cell ":
					delete_indices = len(self.cell) * -1
					del py_list[delete_indices:]
				else:
					del py_list[-1]
				
				string = string[:-2]
				for i in string:
					display_add = i + "\n"
					self.element_display += display_add
				self.element_label.config(text = self.element_display)
				self.ring_space += self.space_list[-1]
				self.space_list = self.space_list[:-1]
				self.space_label.config(text = "Ring space: " + str(self.ring_space))
			else:
				print("Already empty")
		
	def change_beam(self, beam_list, invalid_flag):
		'''Lets user edit the beam settings
		
		Runs if the user presses the "change beam" button, and lets them choose new beam settings by defining a new 
		option_window object. option_window's beam_options() method is run, taking the particle_choice variable as an argument. 
		The ring is not changed during this process. Can also be called if invalid inputs have been found. If a window containing
		the ring display is open, it is closed (done by checking fork_number, which is greater than 1 if a ring display has been
		made). 
		
		----arguments----
		beam_list
		
		---variables/attributes defined inside---
		particle_choice: StringVar object
			stores choice made by user from the menu in the options window
		'''
		if self.fork_number >= 1:
			self.root_2.destroy()
			
		self.options_window = opt_window.Options_Window()
		particle_choice = tk.StringVar(self.root)
		particle_choice.set("proton")
		self.options_window.beam_options(particle_choice)
		self.beam_confirm = tk.Button(self.options_window, text = "Confirm", command = lambda: self.check_beam(beam_list))
		self.beam_confirm.grid()
		
		if invalid_flag == True:
			self.options_invalid_label = tk.Label(self.options_window, text = "Not valid, try again")
			self.options_invalid_label.grid()
		
	def check_beam(self, beam_list):
		'''Validates user inputs from change_beam
		
		Called at the end of change_beam, and validates each input using the bounds defined in option_window's input_list attribute.
		If an invalid value is found, change_beam is called again. If all inputs are valid, gamma and start_coords are set and set_beam 
		is called. invalid_flag and valid are used as before for validation routine, and setting and beam_settings as before for 
		defining the chosen settings for the beam.
		
		----arguments----
		beam_list
		'''
		#sets particle choice as user input
		particle = self.options_window.particle_choice.get().upper()
		
		#validates other inputs
		beam_settings = []
		bounds_list = self.BOUNDS_DICT["beam"]
		beam_settings, invalid_flag, display_message = validation_loop(self.options_window.input_list, bounds_list, beam_settings)
		
		#destroys window and checks if any invalid inputs were found		
		self.options_window.destroy()
		if invalid_flag == False:
			gamma = beam_settings[0]
			start_coords = [beam_settings[1], beam_settings[2], beam_settings[3], beam_settings[4], beam_settings[5], beam_settings[6]]
			self.set_beam(beam_list, particle, gamma, start_coords)
		else:
			self.change_beam(beam_list, True)
	
	def set_beam(self, beam_list, particle, gamma, start_coords):
		'''Sets the chosen and validated beam settings
		
		Updates beam_list with the new settings, either by appending them if the list is empty, or changing indices
		directly if already contains settings. Defines a dictionary of the beam information to be displayed on screen and makes
		widgets using this. If the code has already been run once (fork_number >= 1) and the ring is not being changed too, the 
		previous display is removed before the new one is made. 
		
		Note that all the initial coordinates and momenta are relative to the ideal particle
		
		---arguments----
		beam_list
		particle: str
			particle chosen by user from option menu
		gamma: float
			gamma chosen by user from entry box and validated
		start_coords: list
			list of the start coordinates and momenta of the particle, chosen by user from entry boxes and validated
		
		---variables/attributes defined inside---
		initial_x: float
			initial x-coordinate of particle in the beam
		initial_px: float
			initial momentum in x-direction of particle
		initial_u: float
			initial y-coordinate of particle in the beam
		initial_py: float
			initial momentum in y-direction of particle
		initial_z: float
			initial z-coordinate of particle in the beam
		initial_pz: float
			initial momentum in z-direction of particle
		BEAM_DISPLAY: list of dicts
			contains a list of dictionaries, each containing a widget and its settings
		'''
		#updates beam_list
		if len(beam_list) == 0:
			beam_list.append(particle)
			beam_list.append(gamma)
			beam_list.append(start_coords)
		else:
			beam_list[0] = particle
			beam_list[1] = gamma
			beam_list[2] = start_coords
		
		#defines list of widget dictionaries
		BEAM_DISPLAY = GUI_dicts.make_beam_display(beam_list, start_coords)
		
		#deletes previous display if there is one
		if self.fork_number >= 1 and not self.ring_flag:
			remove_widgets(self.beam_display_list)
		
		#displays beam settings on screen

		self.beam_display_list, input_list = display_widgets(self.root, BEAM_DISPLAY, [], [], 1, 2)
		
	def fork(self, OPAL_list, py_list, beam_list):
		'''Runs OPAL as a child process and updates main window with plots 
		
		Runs when the user presses "execute". Creates the execute_fork method of the runner as a child process using the 
		multiprocessing package and runs it. Increments fork_number, and destroys previous image widgets if OPAL has been 
		run once already (fork_number >= 2). Creates new image widgets from the field maps produced by OPAL, and displays 
		buttons for changing the beam, resetting the ring, or resetting all. 
		
		child: Process object
			multiprocessing process containing the runner's execute_fork method
		
		---variables/attributes defined inside---
			root_2: RingDisplay object
				defined with RingDisplay class
		'''
		#Create child process
		child = mp.Process(target = self.runner.execute_fork, args = (OPAL_list, py_list, beam_list, )) #create child process
		child.run()
		
		self.fork_number += 1
		
		if self.fork_number >= 2:
			if not self.ring_flag:
				self.restart_button.destroy()
				self.cart_img.destroy()
				self.cyl_img.destroy()
				self.root_2.destroy()
			else:
				self.ring_flag = False
		
		self.cart_photo = tk.PhotoImage(file="scaling_ffa_map_cart.png")
		self.cyl_photo = tk.PhotoImage(file="scaling_ffa_map_cyl.png")
		
		self.root_2 = RingDisplay(self.radius, OPAL_list)
		
		#Make new widgets
		self.reset_ring_button = tk.Button(self.root, text = "reset ring", command = lambda: self.reset_ring(OPAL_list, py_list, beam_list))
		self.reset_ring_button.grid(row = 9, column = 0)
		self.reset_beam = tk.Button(self.root, text = "Change beam", command = lambda: self.change_beam(beam_list, False))
		self.reset_beam.grid(row = 6, column = 2)
		self.restart_button = tk.Button(self.root, text = "reset all", command = lambda: self.reset(OPAL_list, py_list, beam_list))
		self.restart_button.grid(row = 2, column = 1)
		
		self.cart_img = tk.Label(self.root, image = self.cart_photo) #update plot images
		self.cart_img.grid(row = 10, column = 0)
		self.cyl_img = tk.Label(self.root, image = self.cyl_photo)
		self.cyl_img.grid(row = 10, column = 2)

class RingDisplay(tk.Toplevel):
	'''Class creating a window that makes a visual representation of the OPAL ring
	'''
	def __init__(self, radius, OPAL_list):
	'''Makes new window as a Toplevel object and sets attributes
	
	----arguments----
		radius: float
			radius of ring
		OPAL_list
	
	---variables/attributes defined inside---
		canvas_2: tkinter canvas object
			canvas on which the ring is drawn
	'''
		super().__init__()
		self.radius = radius
		self.canvas_2 = tk.Canvas(self, width = 600, height = 600)
		self.canvas_2.pack()
		self.draw_OPAL(OPAL_list)

	def draw_OPAL(self, OPAL_list):
		'''Draws the ring and displays the position of all elements in it
		
		Creates a circle in the centre of the screen representing the ring using the Circle class. Iterates through 
		OPAL_list in shared memory space to access the start and end positions of each element in the ring. Finds the 
		angle around the ring of each element using the find_angle function, and plots each element as a square.
		These are created using tkinter polygons, whose first and last vertices are the element's start and end points,
		and whose other vertices are calculated from width and angle. Colour of each element is determined the COLOURS
		dictionary. 
		
		----arguments----
		OPAL_list
		
		---variables/attributes defined inside---
		scale_factor: float
			factor by which the OPAL positions [m] are scaled for the drawing. Calculated from the ring size
		circ_2: Circle object
			circle object which draws a circle on the canvas of the chosen radius
		name: str
			contains the name of the OPAL class of each element (not instantiated)
		start_x, start_y: floats
			x and y coordinates of the element start. OPAL values scaled and offset by centre of circle in canvas
		end_x, end_y: floats
			x and y coordinates of the element end. OPAL values scaled and offset by centre of circle in canvas
		start_angle: float
			angle around the ring that the start point is at [rad]
		end_angle: float
			angle around the ring that the end point is at [rad]
		angle_diff: float
			angular width of element in ring [rad]
		width: float
			distance taken up in ring by element
		x_1, y_1: floats
			coordinates of the second polygon point (above start point)
		x_2, y_2: floats
			coordinates of third polygon point (above end point)
		colour: str
			colour of the element from COLOURS dictionary
		points: list
			contains the coordinates of each polygon vertex
		element: tkinter polygon
			polygon drawn on canvas
		'''
		scale_factor = 300 / (1.5*self.radius)
		circle_radius = self.radius * scale_factor
		self.circ_2 = Circle(self.canvas_2, circle_radius, self)
		
		for i in range(0, len(OPAL_list)):
			name = OPAL_list[i][0]
			start_x = (OPAL_list[i][1][0] * scale_factor) + 300
			start_y = (-(OPAL_list[i][1][1]) * scale_factor) + 300
			end_x = (OPAL_list[i][2][0] * scale_factor) + 300
			end_y = (-(OPAL_list[i][2][1]) * scale_factor) + 300
			
			start_angle = self.find_angle(start_x, start_y)
			end_angle = self.find_angle(end_x, end_y)
			angle_diff = np.abs(start_angle - end_angle)
			width = circle_radius * np.sqrt(2*(1 - np.cos(angle_diff)))
			
			x_1 = start_x + width * np.cos(start_angle)
			y_1 = start_y + width * np.sin(start_angle)
			x_2 = end_x + width * np.cos(start_angle)
			y_2 = end_y + width * np.sin(start_angle)
			
			colour = COLOURS[name]
			points = [start_x, start_y, x_1, y_1, x_2, y_2, end_x, end_y]
			element = self.canvas_2.create_polygon(points, fill = colour)
			
	def find_angle(self, x, y):
		'''Find angle around the ring of a given point 
		
		Takes the coordinates of a point and the radius of the ring and returns the angle around the ring
		the point is at. Calculates using the cosine rule. 
		
		----arguments----
		x: float
			x_coordinate of point
		y: float
			y_coordinate of point
		
		----returns----
		angle: float
			angle around the ring the point is at [rad]
		'''
		delta_x = x - (300 + self.radius)
		delta_y = y - 300
		length_a = np.sqrt(delta_x ** 2 + delta_y ** 2)
		length_b = np.sqrt((delta_x + self.radius)**2 + delta_y **2)
		cos_angle = (self.radius**2 + length_b **2 - length_a **2)/(2*self.radius*length_b)
		angle = np.arccos(cos_angle)
		if delta_y < 0:
			angle = (2*np.pi) - angle
		return angle
			
class Circle:
	'''Class containing the circle representing the ring
	'''
	def __init__(self, canvas, radius, root):
		'''
		Draws a ring at the centre of the canvas with the radius selected. 
		
		root: tkinter TopLevel object
			window on which the circle is drawn
		canvas: tkinter canvas object
			canvas on which circle is drawn
		radius: float
			taken as an argument. The radius of the ring determined by the user input
		centre_x, centre_y: ints
			the x and y coordinates of the centre of the circle (currently hard-coded)
		circ: tkinter circle
			circle drawn on the canvas by tkinter
		'''
		self.root = root
		self.canvas = canvas
		self.radius = radius
		self.centre_x = 300
		self.centre_y = 300
		self.circ = self.canvas.create_oval(self.centre_x - radius, self.centre_y - radius, self.centre_x + radius, self.centre_y + radius)

def validate_input(user_input, lower_bound, upper_bound):
	'''Validates the user input according to bounds
	
	Checks if input is numerical, and prints an error message and returns None if not. If numerical, checks number is within 
	the bounds given. If not, an error message is printed and None returned. If it is within the bounds, the input is valid and
	the validated float is returned.
	
	----arguments----
	user_input: str
		the inputted value to be validated
	lower_bound: float
		lower bound
	upper_bound: float
		upper bound
	
	----returns----
	valid: float
		validated input value
	'''
	try:
		user_input = float(user_input)
	except: 
		print("Must be numerical")
		return None, "must be numerical"
	if user_input >= lower_bound and user_input <= upper_bound:
		return user_input, None
	else:
		print("not in bounds")
		return None, "not in bounds"

def validation_loop(input_list, bounds_list, settings_list):
	'''Validates a set of inputs according to their bounds
	
	Iterates through a given list of input widgets and gets the value enterred. Iterates through all inputs and validates them, 
	setting invalid_flag and an error message accordingly. Bounds specified in arguments. Valid inputs appended to a chosen list.
	
	----arguments----
		input_list: list
			list of tkinter input widgets
		bounds_list: list
			list containing the bounds for each input. Structure is [[lower_bound, upper_bound]]
		settings_list: list
			list to which valid inputs are appended
	
	----returns----
		settings_list: list
			settings_list after inputes appended
		invalid_flag: Bool
			True if any invalid inputs were encountered, False otherwise
		display_message: str
			error message to be displayed. "" if no invalid inputs
	'''
	invalid_flag = False
	display_message = ""
	for i in range(0, len(input_list)):
			setting = input_list[i].get()
			lower_bound = bounds_list[i][0]
			upper_bound = bounds_list[i][1]
			valid, message = validate_input(setting, lower_bound, upper_bound)
			
			if valid == None:
				invalid_flag = True
				display_message = message
			else:
				settings_list.append(valid)
			
	return settings_list, invalid_flag, display_message

def display_widgets(root, widget_dict, widget_list, input_list, offset, col):
	'''Displays a list of widgets on screen
	
	Iterates through a list of widget dictionaries, instantiating an object of each widget given and 
	setting its args to those stored. Creates a list of all widgets, and a list of input widgets only.
	
	----arguments----
	root: tk Root object
		the window the widgets are displayed in
	widget_list: list
		list of widgets to be appended to 
	input_list: list
		list of input widgets to be appended to
	offset: int
		offset from row 0 used by the grid method in the loop
	col: int
		column
	
	----returns----
	widget_list:
		widget_list with all elements added
	input_list:
			input_list with all elements added	
	'''
	for i in range(0, len(widget_dict)):
		widget_type = widget_dict[i]["widget"]
		options = widget_dict[i]["options"]
		widget = widget_type(root, **options)
		widget.grid(row = i + offset, column = col)
		widget_list.append(widget)
		if widget_type == tk.Scale or widget_type == tk.Entry:
			input_list.append(widget)
	return widget_list, input_list

def remove_widgets(widget_list):
	'''Deletes all widgets in a given list
	
	----arguments----
	widget_list: list
		list of widgets to be deleted
	'''
	for i in widget_list:
		i.destroy()

def main():
	"""Defines the manager and lists in shared memory, then runs main code sequence
	
	Defines a mulitprocessing Manager object, and runs the main code sequence with this as the manager. Creates OPAL_list, py_list,
	and beam_list in shared memory between the manager and other processes. The GUI object is then defined, and the root it defines 
	taken through its main loop. 
	
	---variables/attributes defined inside---
	py_list: manager list
		 contains the information on what elements have been added by the user and the settings selected for them. Built in python, 
		 and then used by OPAL to create the ring. structure is [[{"element_type": OPAL class name}, settings], ....]
	OPAL_list: manager list
		contains the name, start position, and end position of every element in the OPAL ring. Built up in OPAL, then used by python
		to draw the ring OPAL generated. Structure is [[name, element_start, element_end], ....]
	beam_list: manager list
		contains the beam/distribution settings selected by the user. Built up in python, then used by OPAL when defining the beam
		and distribution objects. Structure is [particle, gamma, [start_coords]]
	"""
	with mp.Manager() as manager:
		py_list = manager.list([])
		OPAL_list = manager.list([])
		beam_list = manager.list([])
		window = Gui(OPAL_list, py_list, beam_list)
		window.root.mainloop()
		print("Finished\n\n")
		input("Press <Enter> to finish")
		
if __name__ == "__main__":
	main()
