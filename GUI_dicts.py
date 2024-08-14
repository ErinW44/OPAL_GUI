'''
Module containing all constant dictionaries, and functions for creating all dictionaries whose values depend on GUI / OPAL
variables. 
'''
import tkinter as tk
import sys

MAX_FLOAT = sys.float_info.max
MIN_FLOAT = sys.float_info.min

BEAM_SETUP = [
  {
    "widget": tk.Label,
    "options": {
      "text": "Beam gamma (above 1)"
    }
  },
  {
    "widget": tk.Entry,
    "options": {}
  },
  {
    "widget": tk.Label,
    "options": {
      "text": "Initial x [m]"
    }
  },
  {
    "widget": tk.Entry,
    "options": {}
  },
  {
    "widget": tk.Label,
    "options": {
      "text": "Initial px [GeV/c]"
    }
  },
  {
    "widget": tk.Entry,
    "options": {}
  },
  {
    "widget": tk.Label,
    "options": {
      "text": "Initial y [m]"
    }
  },
  {
    "widget": tk.Entry,
    "options": {}
  },
  {
    "widget": tk.Label,
    "options": {
      "text": "Initial py [GeV/c]"
    }
  },
  {
    "widget": tk.Entry,
    "options": {}
  },
  {
    "widget": tk.Label,
    "options": {
      "text": "Initial z [m]"
    }
  },
  {
    "widget": tk.Entry,
    "options": {}
  },
  {
    "widget": tk.Label,
    "options": {
      "text": "Initial pz [GeV/c]"
    }
  },
  {
    "widget": tk.Entry,
    "options": {},
  }
]

COLOURS_KEY ={
    "ScalingFFAMagnet": [
    						"red", 
    						"Scaling FFA magnet"
    					],
    "DefaultDrift": [
    						"blue", 
    						"Default drift"
    					],
    "LOCAL_CARTESIAN_OFFSET": [
    						"blue", 
    						"drift"
    					],
    "MULTIPOLET": [
    						"green", 
    						"multipole"
    					],
    "VARIABLE_RF_CAVITY": [
    						"yellow", 
    						"RF cavity"
    					]
  }
  
def define_bounds_dict(radius, ring_space):
	'''Makes dictionary of all elements and the bounds of each of their settings.
	
	----arguments----
	radius: float
		radius of ring
	ring_space: float
		space remaining in the ring
	
	----returns----
	bounds_dict: dict
		dictionary containing bounds for each setting of every element (and the beam). Structure
		is {"element name": [[lower, upper], ...], ....}
	'''
	bounds_dict = {
		"beam": [
		  [1.00000001,
      	   MAX_FLOAT
      	  ],
      	  [-MAX_FLOAT,
      	   MAX_FLOAT
      	  ],
      	  [-MAX_FLOAT,
      	   MAX_FLOAT
      	  ],
      	  [-MAX_FLOAT,
      	   MAX_FLOAT
      	  ],
      	  [-MAX_FLOAT,
      	   MAX_FLOAT
      	  ],
      	  [-MAX_FLOAT,
      	   MAX_FLOAT
      	  ],
      	  [-MAX_FLOAT,
      	   MAX_FLOAT
      	  ]
      	],
		"Scaling FFA magnet": [
		  [
		    -2,
		    2
		  ],
		  [
		    MIN_FLOAT,
		    10
		  ],
		  [
		    MIN_FLOAT,
		    radius/4
		  ],
		  [
		    MIN_FLOAT,
		    radius/40
		  ],
		  [
		    MIN_FLOAT,
		    radius/4
		  ],
		  [
		    MIN_FLOAT,
		    radius
		  ],
		  [
		    MIN_FLOAT,
		    radius
		  ]
		],
		"Drift": [
		  [
		    MIN_FLOAT,
		    ring_space/radius
		  ]
		],
		"RF Cavity": [
		  [
		    0,
		    MAX_FLOAT
		  ],
		  [
		    0,
		    MAX_FLOAT
		  ],
		  [
		    0,
		    MAX_FLOAT
		  ],
		  [
		    0,
		    MAX_FLOAT
		  ],
		  [
		    0,
		    MAX_FLOAT
		  ],
		  [
		    0,
		    MAX_FLOAT
		  ],
		  [
		    0,
		    MAX_FLOAT
		  ],
		  [
		    0,
		    MAX_FLOAT
		  ],
		  [
		    0,
		    MAX_FLOAT
		  ]
		],
		"RF more": [
		  [
		   	MIN_FLOAT,
		   	ring_space
		  ],
		  [
		  	MIN_FLOAT,
		  	radius
		  ],
		  [
		  	MIN_FLOAT,
		  	radius
		  ]
		 ], 
		"Multipole": [
		  [
		    0,
		    ring_space
		  ],
		  [
		    0,
		    radius
		  ],
		  [
		    0,
		    radius
		  ],
		  [
		    0,
		    5
		  ]
		],
	   "Multipole more": [
		  [
		    -2,
		    2
		  ],
		  [
		    -2,
		    2
		  ],
		  [
		    -2,
		    2
		  ],
		  [
		    -2,
		    2
		  ],
		  [
		    -2,
		    2
		  ]
		]
	  }
	
	return bounds_dict

def make_beam_display(beam_list, start_coords):
	'''Makes the list of widget dictionaries used to display the beam settings
	
	----arguments----
	beam_list: list
		one of the lists in shared memory from the GUI code
	start_coords: list
		list of the start coordinates and momenta for the particle in the beam
		
	----returns----
	beam_display: list
		contains a list of dictionaries, each containing a widget and its settings. Structure is
		[{"widget": OPAL class name, "options": {args}, ...]
	'''
	beam_display = [
		{
			"widget":tk.Label, 
			"options":{
			"text":"----Beam----"
			}
		},
		{
			"widget":tk.Label, 
			"options":{
			"text":"particle type: " + beam_list[0]
			}
		}, 
		{
			"widget":tk.Label, 
			"options":{
			"text":"Beam gamma: " + str(beam_list[1])
			}
		}, 
		{
			"widget":tk.Label, 
			"options":{
			"text":"initial coordinates: " + 	str(start_coords)
			}
		}
	]
	
	return beam_display

def make_all_options(max_length, max_angle, radius):
	'''Make dictionary of every element and the widgets used to get user input for their settings
	
	----arguments----
	max_length: float
		maximum length an element can be and still fit in ring
	max_angle: float
		maximum angle an element can take up (from centre of ring) and still fit in ring
	radius: float
		radius of ring
	
	----returns----
	all_options: dict
			dictionary containing the list of widgets for each element. Structure is 
			{"name of element":[{"widget": tkinter widget object, "options"{dict of widget arguments},....}],....}
	'''
	all_options = {
		"Scaling FFA magnet": [
			{
				"widget":tk.Label, 
				"options": {
					"text":"b0 (-2 to 2 T)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"field index (0 to 10)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			},
			{
				"widget":tk.Label, 
				"options": {
					"text":"start length (0 to " + str(radius/4) + " m)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options": {
					"text":"centre length (0 to " + str(radius/40) + " m)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options": {
					"text":"end length (0 to " + str(radius/4) + " m)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			},
			{
				"widget":tk.Label, 
				"options": {
					"text":"radial positive extent (0 to " + str(radius) + " [m])"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			},
			{
				"widget":tk.Label, 
				"options": {
					"text":"radial negative extent (0 to " + str(radius) + " [m])"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}
		],
		"Drift":[
			{
				"widget":tk.Label, 
				"options":{
				"text":"Angle (0 to " + str(max_angle) + " rad)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}
		],
		"RF Cavity":[
			{
				"widget":tk.Label, 
				"options":{
					"text":"Polynomial time dependence coefficients"
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"Phase"
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"p0"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"p1"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"p3"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"Amplitude"
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"p0"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"p1"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"p3"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"Frequency"
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"p0"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"p1"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"p3"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}
		],
		"RF more":[
			{
				"widget":tk.Label, 
				"options":{
					"text":"length (0 to " + str(max_length) + " m)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"width (0 to " + str(radius) + " m)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"height (0 to " + str(radius) + " m)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}
		],
		"Multipole":[
			{
				"widget":tk.Label, 
				"options":{
					"text":"length (0 to " + str(max_length) + " m)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"horizontal aperture (0 to " + str(radius) + " m)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"vertical aperture (0 to " + str(radius) + " m)"
					}
			}, 
			{
				"widget":tk.Entry, 
				"options":{
					}
			}, 
			{
				"widget":tk.Label, 
				"options":{
					"text":"number of  orders"
					}
			}, 
			{
				"widget":tk.Scale, 
				"options":{
					"from_":1, "to":4, "resolution":1, "orient":tk.HORIZONTAL
					}
			}
		]
	}
	
	return all_options

	
