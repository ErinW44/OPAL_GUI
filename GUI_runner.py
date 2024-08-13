#import modules
import pyopal.elements.local_cartesian_offset
import pyopal.elements.scaling_ffa_magnet
import pyopal.elements.multipolet
import pyopal.elements.asymmetric_enge
import pyopal.elements.probe
import pyopal.objects.field
import pyopal.elements.polynomial_time_dependence
import pyopal.elements.variable_rf_cavity
import pyopal.objects.minimal_runner
import os
import pyopal.elements.scaling_ffa_magnet
import test_track_run_scaling_ffa
import math
import ffa_field_mapper_2
import matplotlib.pyplot

class Runner(test_track_run_scaling_ffa.ScalingFFARunner):
	def __init__(self, OPAL_list, py_list, beam_list):
		'''Defines the runner object used by the GUI
		
		Inherits from the runner used in test_track_run_scaling_ffa.py, which in turn inherits from the original minimal 
		runner class defined by OPAL. 
		'''
		super().__init__()
		self.verbose = 1
	
	def make_beam(self, beam_list):
		"""Make a beam object
		
		The beam holds the global/default beam distribution information, such as the gamma value of the beam etc. Some of these are
		selected by the user in the GUI code. 
		
		----arguments----
		beam_list
		
		---variables/attributes defined inside---
		beam: OPAL object
			OPAL beam object
		particle: str
			particle type used in beam (chosen by user, accessed from beam_list)
		momentum: float
			momentum of beam
		gamma: float
			gamma value of beam (chosen by user, accessed from beam_list)
		beam_frequency: float
			frequency of beam. Set to default value here (maybe add option to choose it?)
		number_of_slices: int
			number of slices in a bunch. Set to default value here (maybe add option to choose?)
		momentum_tolerance: bool
			enables or disables momentum tracking. Set to 0 here 
		"""
		
		beam = pyopal.objects.beam.Beam()
		beam.set_opal_name("DefaultBeam")
		beam.particle = beam_list[0].upper()
		beam.momentum = self.momentum
		beam.gamma = beam_list[1]
		beam.beam_frequency = 1e-6/self.time_per_turn # MHz
		beam.number_of_slices = 10
		beam.number_of_particles = int(self.distribution_str.split()[0])
		beam.momentum_tolerance = 0  # disable momentum checking
		beam.register()
		self.beam = beam
        	
	def make_time_dependence(self, name, pol0, pol1, pol2):
		'''Make a polynomial time dependence object
		
		Make an OPAL polynomial time dependence object with the coefficients chosen by the user in the GUI/option_window code.
		
		----arguments----
		name: str
			name of object
		pol0: float
			polynomial coefficient 0 (chosen by user)
		pol1: float
			polynomial coefficient 1 (chosen by user)
		pol2: float
			polynomial coefficient 2 (chosen by user)
		'''
		time_dep = pyopal.elements.polynomial_time_dependence.PolynomialTimeDependence()
		time_dep.p0 = pol0
		time_dep.p1 = pol1
		time_dep.p2 = pol2
		time_dep.set_opal_name(name)
		time_dep.update()
		return time_dep
		
	def make_line(self, py_list):
		"""Make a Line object, which holds a sequence of beam elements. 
		
		Overloads minimal_runner method so py_list is an argument.
		
		----arguments----
		py_list
		"""
		self.line = pyopal.objects.line.Line()
		self.line.set_opal_name("DefaultLine")
		try:
			self.line.append(self.ring)
		except Exception:
			print(self.ring_error)
			raise
		self.line.append(self.null_drift())
		an_element_iter = self.make_element_iterable(py_list)
		for element in an_element_iter:
			self.line.append(element)
		self.line.register()
        
	def execute(self, py_list, OPAL_list, beam_list):
		'''Executes OPAL
		
		Overloads minimal_runner method so it builds up OPAL_list by adding the name, start and end coordinates of each element 
		in the ring. Runs OPAL methods in sequence. 
		
		----arguments----
		py_list
		OPAL_list
		beam_list
		
		---variables/attributes defined inside---
		element_num: int
			number of elements in the ring, accessed by the get_number_of_elements method of the field object
		name: str
			name of element
		element_start: list
			(x,y,z) coordinates of the start of the element
		element_end:
			(x,y,z) coordinates of the end of the element
		'''
		here = os.getcwd()
		OPAL_list *= 0
		try:
			os.chdir(self.tmp_dir)
			self.make_option()
			self.make_distribution(beam_list)
			self.make_field_solver()
			self.make_beam(beam_list)
			self.make_ring()
			self.make_line(py_list)
			
			#maybe add code here to give OPAL_list to GUI and draw the elements, then click to proceed with making plots?
			
			self.make_track()
			self.make_track_run()
			if self.run_name:
				self.track_run.set_run_name(self.run_name)
			self.preprocess()
			self.track_run.execute()
			
			element_num = pyopal.objects.field.get_number_of_elements()
			for i in range(0, element_num):
				name = pyopal.objects.field.get_element_name(i)
				element_start = pyopal.objects.field.get_element_start_position(i)
				element_end = pyopal.objects.field.get_element_end_position(i)
				OPAL_list.append([name, element_start, element_end])	
			self.postprocess()
		except:
			raise
		finally:
			if self.verbose:
				print("Finished running in directory", os.getcwd())
			os.chdir(here)
			
	def execute_fork(self, OPAL_list, py_list, beam_list):
		'''Forks 
		
		Overloads minimal_runner's execute fork so it takes the lists in shared memory as arguments
		
		----arguments----
		OPAL_list
		py_list
		beam_list
		'''
		a_pid = os.fork()
		if a_pid == 0: # the child process
			self.execute(py_list, OPAL_list, beam_list)
			os._exit(self.exit_code)
		else:
			retvalue = os.waitpid(a_pid, 0)[1]
			return retvalue
            
	def make_element_iterable(self, py_list):
		""" Return an iterable (e.g. list) of elements to append to the line
		
		Overload the method in MinimalRunner to place the field elements in the lattice. Iterates through py_list and
		adds elements to the ring list. Note RF cavites are handled differently, as the time dependences are OPAL objects 
		and can't be stored in py_list. Thus, they must be defined as part of the pyOpal code here. 
		
		----arguments----
		py_list
		
		----returns----
		ring + probes: list
			list of elements and probes in the ring
		
		---variables/attributes defined inside---
		probes: list
			list of OPAL Probe objects. Set without user input here (maybe change?)
		ring: list
			list of OPAL element objects in the ring
		ElementClass: str
			name of the class of the current element
		new_element: OPAL element object
			instantiated version of the current element with default attributes
		args: dict
			dictionary containing the arguments for the current element
		phase, voltage, frequency: time dependence objects
			time dependence objects defined with user inputs for each of the phase, voltage and time arguments
			of the RF cavity
		
		for each of phase, amplitude and frequency:
		p0: float
			p0 coefficient
		p1: float
			p1 coefficient
		p2: float
			P2 coefficient
		"""
		probes = [self.build_probe(360.0/self.n_cells*i) for i in range(self.n_cells)]
		ring = []
		for i in range(0, len(py_list)):
			if py_list[i][0]["element_type"] == pyopal.elements.variable_rf_cavity.VariableRFCavity:
				phase_p0 = py_list[i][1]["phase_p0"]
				phase_p1 = py_list[i][1]["phase_p1"]
				phase_p2 = py_list[i][1]["phase_p2"]
				
				amp_p0 = py_list[i][1]["amp_p0"]
				amp_p1 = py_list[i][1]["amp_p1"]
				amp_p2 = py_list[i][1]["amp_p2"]
				
				freq_p0 = py_list[i][1]["freq_p0"]
				freq_p1 = py_list[i][1]["freq_p1"]
				freq_p2 = py_list[i][1]["freq_p2"]
				
				self.phase = self.make_time_dependence("phase", phase_p0, phase_p1, phase_p2)
				self.voltage = self.make_time_dependence("voltage", amp_p0, amp_p1, amp_p2)
				self.frequency = self.make_time_dependence("frequency", freq_p0, freq_p1, freq_p2)
				
				args = {"length": py_list[i][1]["length"], "width":py_list[i][1]["width"], "height":py_list[i][1]["height"]}
				args.update({"frequency_model":"frequency", "phase_model":"phase", "amplitude_model":"voltage"})
				new_element = pyopal.elements.variable_rf_cavity.VariableRFCavity()
				new_element.set_attributes(**args)
			else:
				ElementClass = py_list[i][0]["element_type"]
				new_element = ElementClass()
				args = py_list[i][1]
				new_element.set_attributes(**args)
			
			ring.append(new_element)
			
		return ring+probes
	
	def make_distribution(self, beam_list):
		"""Make a distribution
		
		Defines distribution_str from the start coordinates and momenta in beam_list. Makes the initial beam distribution
		of the PyOPAL simulation. Uses the FROMFILE type, with the file containing only distribution_str (makes 1 particle 
		with chosen start coordinates and momenta). 
		
		----arguments----
		beam_list
		
		----returns----
		distribution: OPAL object
		
		---variables/attributes defined inside---
		distribution_str: str
			string containing start coordinates and momenta of particle.
		dist_file: file object
			file that distribution_str is written to and then read from
		distribution_str: str
			the string containing the initial coordinates and momenta of the particle, correctly formatted for OPAL 
		"""
		start_coords = beam_list[2]
		
		initial_x = start_coords[0]
		initial_px = start_coords[1]
		initial_y = start_coords[2]
		initial_py = start_coords[3]
		initial_z = start_coords[4]
		initial_pz = start_coords[5]
		
		#defines distribution string
		self.distribution_str = "1 \n"+str(initial_x) + " " +str(initial_px) + " "+str(initial_y) + " "+str(initial_py) + " "+str(initial_z) + " " +str(initial_pz) + " "		
		
		dist_file = open(self.distribution_filename, "w+")
		dist_file.write(self.distribution_str)
		dist_file.flush()
		dist_file.close()
		self.distribution = pyopal.objects.distribution.Distribution()
		self.distribution.set_opal_name("DefaultDistribution")
		self.distribution.type = "FROMFILE"
		self.distribution.filename = self.distribution_filename
		self.distribution.register()
		return self.distribution
        	
	def plots(self, plot_dir = None):
		"""Make plots showing rectangular and cylindrical field maps
		
		Overloads test_track_run_scaling_ffa.py runner method by defining a mapper from a different file. This mapper is 
		different from the original in that it plots the beam trajectory on the cartesian field map.
		
		---variables/attributes defined inside---
		mapper: object
			instance of FFAFieldMapper class from object from ffa_field_mapper_2.py
		"""
		
		mapper = ffa_field_mapper_2.FFAFieldMapper()
		mapper.plot_dir = self.plot_dir
		mapper.load_tracks(os.path.join(self.tmp_dir, self.run_name+"-trackOrbit.dat"))

		mapper.radial_contours = [
			{"radius":self.r0, "linestyle":"dashed", "colour":"grey", "label":"r0"},
			{"radius":self.r0-self.dr/2, "linestyle":"-", "colour":"grey", "label":"r0-\nradial_neg_extent"},
			{"radius":self.r0+self.dr/2, "linestyle":"-", "colour":"grey", "label":"r0+\nradial_pos_extent"},
		]


		phi_start = (self.f_start/self.r0)*180/math.pi
		phi_middle = ((self.f_start+self.f_centre_length/2)/self.r0)*180/math.pi
		phi_fringe_end = ((self.f_start+self.f_centre_length)/self.r0)*180/math.pi
		phi_end = (self.f_end/self.r0)*180/math.pi
		mapper.spiral_contours = [
			{"phi0":phi_start, "r0":self.r0, "spiral_angle":self.spiral_angle*180/math.pi, "linestyle":"dashed", "colour":"blue", "label":"magnet_start"},
			{"phi0":phi_middle, "r0":self.r0, "spiral_angle":self.spiral_angle*180/math.pi, "linestyle":"dashed", "colour":"grey", "label":"magnet_start+\ncentre_length/2"},
			{"phi0":phi_fringe_end, "r0":self.r0, "spiral_angle":self.spiral_angle*180/math.pi, "linestyle":"dashed", "colour":"grey", "label":"magnet_start+\ncentre_length"},
			{"phi0":phi_end, "r0":self.r0, "spiral_angle":self.spiral_angle*180/math.pi, "linestyle":"dashed", "colour":"blue", "label":"magnet_end"},
		]

		mapper.r_points = [self.r0+i*0.001 for i in range(-1200, 1200+1, 2)]
		mapper.phi_points = [i/8.0 for i in range(0, 180+1, 2)]
		mapper.field_map_cylindrical()

		mapper.x_points = [i*0.05 for i in range(-100, 100+1, 1)]
		mapper.y_points = [i*0.05 for i in range(-100, 100+1, 1)]

		mapper.field_map_cartesian()
		mapper.oned_field_map(self.r0)

		n_elements = pyopal.objects.field.get_number_of_elements()

