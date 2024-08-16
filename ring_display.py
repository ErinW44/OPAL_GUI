'''File containing the RingDisplay class

Contains the RingDisplay class, which is used to make a window with a visual representation of how OPAL has placed
elements around the ring drawn on it. The file also contains the Circle class, which draws a circle in the middle of 
the canvas with the radius defined by the user.

The RingDisplay class is called by the Gui class after OPAL is run. The method draw_OPAL uses OPAL list to draw each 
element on a canvas in its window (details in docstring). The class also contains a method for finding the angle around
the ring an element is at.  
'''

import numpy as np
import tkinter as tk
import GUI_dicts

COLOURS_KEY = GUI_dicts.COLOURS_KEY

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
		
		Creates a circle in the centre of the screen using the Circle class. Iterates through OPAL_list to access the 
		start and end positions of each element in the ring. Finds the angle around the ring of each element using the
		find_angle function, and plots each element as a square. These are created using tkinter polygons, whose first 
		and last vertices are the element's start and end points, and whose other vertices are calculated from width and
		angle. Colour of each element is determined the COLOURS_KEY dictionary. 
		
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
			length_to_corner: float
				length from origin to first corner of element
			colour: str
				colour of the element from COLOURS_KEY dictionary
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
			
			if start_angle > end_angle:
				end_angle += 2 * np.pi
			
			angle_diff = np.abs(start_angle - end_angle)
			width = circle_radius * np.sqrt(2*(1 - np.cos(angle_diff)))
			length_to_corner = np.sqrt(width**2 + circle_radius**2 - 2*width*circle_radius*np.cos(np.pi - angle_diff/2))
			
			x_1 = (length_to_corner * np.cos(start_angle + angle_diff/4)) + 300
			y_1 = -(length_to_corner * np.sin(start_angle + angle_diff/4)) + 300
		
			x_2 = end_x + x_1 - start_x
			y_2 = end_y + y_1 - start_y			
			
			colour = COLOURS_KEY[name][0]
			points = [start_x, start_y, x_1, y_1, x_2, y_2, end_x, end_y]
			element = self.canvas_2.create_polygon(points, fill = colour)
		
		self.make_key()
			
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
		if delta_y > 0:
			angle = (2*np.pi) - angle
		return angle
	
	def make_key(self):
		self.key_label = tk.Label(self, text = "")
		self.key_text = "---key---\n"
		self.key_label.pack()
		for key in COLOURS_KEY:
			self.key_text += COLOURS_KEY[key][1] + ": " + COLOURS_KEY[key][0] + "\n"
		self.key_label.configure(text = self.key_text)
		
class Circle:
	'''Class containing the circle representing the ring
	'''
	def __init__(self, canvas, radius, root):
		'''
		Draws a ring at the centre of the canvas with the radius selected. 
		
		----arguments----
		canvas: tkinter canvas object
			canvas on which circle is drawn
		root: tkinter TopLevel object
			window on which the circle is drawn
		radius: float
			taken as an argument. The radius of the ring determined by the user input
		
		---variables/attributes defined inside---
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
