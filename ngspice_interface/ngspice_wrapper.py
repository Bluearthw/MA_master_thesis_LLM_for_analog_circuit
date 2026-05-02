import os
import re
import yaml
import random
import string
import time 
import sys
sys.path.append(".")
from utils import gen_utils as utils_agent
from genai_agent import local_config 
class NgspiceWrapper(object):
    
    def __init__(self, path_yaml = ""):
        self.with_yaml = False
        if path_yaml != "":
            self.with_yaml = True
            self.path_yaml = path_yaml
            with open(path_yaml, 'r') as f:
                yaml_data = yaml.load(f, Loader=yaml.Loader)
            self.circuit_name = yaml_data['circuit_name']
            self.circuit_multipliers = yaml_data['circuit_multipliers']
            self.technology = yaml_data['technology']
            project_path = os.getcwd()
            
            # self.netlist_path = os.path.join(project_path, 'ngspice_interface', 'files', 'input_netlists', f"{self.circuit_name}.cir")
            self.netlist_path = local_config.path_output + f"{self.circuit_name}/" + "final_netlist.cir"
            self.solutions_folder = os.path.join(project_path, 'no_backup', 'solutions')
            self.output_netlists_folder = os.path.join(project_path, 'no_backup', 'output_netlists')
            self.output_files_folder = os.path.join(project_path, 'no_backup', 'output_files')
            self.param_names = yaml_data['params'].keys()
            self.parameters = {}
            self.read_netlist()
        
        
        # paths
        self.path_ac_gain = None 
        self.path_psrr = None
        self.path_noise = None
        self.path_trans = None

        self.freq = None
        self.current = None

        # store gain as complex and compute magnitude/phase
        self.vout_complex = None
        self.vout_mag = None
        self.mag_db = None
        self.phase = None

        self.psrr_db = 0

        self.data_trans = None

        #differential output
        self.path_adm = None
        self.path_acm = None
        self.vout1_complex = None
        self.vout2_complex = None
        self.phase_v1 = None # for output balance
        self.phase_v2 = None
        
    def read_netlist(self):
        with open(self.netlist_path, 'r') as f:
            for line in f:
                if line.startswith(".param"):  # Find parameter lines
                    match = re.search(r"(\w+)=([\w\.]+(?:e[+-]\d+)?)", line)
                    if match:
                        param_name = match.group(1)
                        param_value = match.group(2)
                        units = {'f':1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'meg': 1e6, 'g': 1e9}
                        if param_name in ["trf", "period", "VDD"]:
                            value = None
                            for unit, multiplier in units.items():
                                if unit in param_value:
                                    value = float(param_value.rstrip(unit)) * multiplier
                                    break
                            if value is None:  # If no unit was found, just convert the value to float
                                value = float(param_value)
                            setattr(self, param_name, value)
                        elif param_name in self.param_names:
                            value = None
                            for unit, multiplier in units.items():
                                if unit in param_value:
                                    value = float(param_value.rstrip(unit)) * multiplier
                                    break
                            if value is None:  # If no unit was found, just convert the value to float
                                value = float(param_value)
                            self.parameters[param_name] = value

    def generate_random_name(self, length=10):
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters) for _ in range(length))
        timestamp = str(int(time.time()))
        unique_name = timestamp + "_" + random_string
        return unique_name

    def create_new_netlist(self, parameters=None, process='TT', temp_pvt=None, vdd=None, vcm=None, vhigh=None):
        # Define the new netlist path randomly
        self.random_name = self.circuit_name + f"_{self.generate_random_name()}"
        new_netlist_path = os.path.join(self.output_netlists_folder, self.random_name + ".cir")
        self.circuit_params = parameters
        
        # Open the input netlist and read lines
        with open(self.netlist_path, 'r') as input_file:
            lines = input_file.readlines()
        
        # Modify the lines
        for i, line in enumerate(lines):
            if line.startswith(".param"):  # Find parameter lines
                # Split the line into individual parameter assignments
                param_assignments = re.findall(r"(\w+)=([\w\.]+(?:e[+-]\d+)?)", line)
                new_assignments = []
                for param_name, old_value in param_assignments:
                    if parameters is not None and param_name in parameters:
                        new_value = str(parameters[param_name])
                    elif param_name == "temp_pvt" and temp_pvt is not None:
                        new_value = str(temp_pvt)
                    elif param_name in ["VREF", "ICMV"] and vcm is not None:
                        new_value = str(vcm)
                    elif param_name == "VHIGH" and vhigh is not None:
                        new_value = str(vhigh)
                    elif param_name == "VDD" and vdd is not None:
                        new_value = str(vdd)
                        self.VDD = new_value
                    else:
                        new_value = old_value
                    new_assignments.append(f"{param_name}={new_value}")
                
                # Reconstruct the line with updated values
                lines[i] = ".param " + " ".join(new_assignments) + "\n"
            
            elif line.startswith(".include"):  # Find include lines
                match = re.search(r"(\w+_\w+\.sp)", line)
                if match:
                    old_model_path = match.group(1)
                    new_model_path = re.sub(r"_\w+\.sp", f"_{process}.sp", old_model_path)
                    lines[i] = line.replace(old_model_path, new_model_path)  # Replace the model path
            
            elif line.startswith("wrdata"):  # Find wrdata lines
                match = re.search(r"wrdata (\w+)\.csv", line)
                if match:
                    old_file_name = match.group(1)
                    new_file_name = os.path.join(self.output_files_folder, old_file_name.split('_')[0] + "_" + self.random_name)
                    lines[i] = line.replace(old_file_name, new_file_name)
        
        # Open the new netlist and write lines
        os.makedirs(os.path.dirname(new_netlist_path), exist_ok=True)
        with open(new_netlist_path, 'w') as output_file:
            output_file.writelines(lines)
        
        return new_netlist_path

    def simulate(self, netlist_path):
        succeed = 0 # this means no error occurred
        nl = utils_agent.get_file_to_str(netlist_path)
        # print(netlist_path)
        sim_output = utils_agent.run_ngspice_direct(nl, False, netlist_path)
        # print(sim_output)
        if not sim_output["success"]:
            # raise RuntimeError('program {} failed!'.format(command))
            succeed = sim_output["message"] # this means an error has occurred
            print("ngspice_wrapper: ngspice sim error")
        return succeed
    

    def measure_metrics(self):
        result = None
        return result



if __name__ == "__main__":
    project_path = os.getcwd()
    path_yaml = os.path.join(project_path, 'ngspice_interface', 'files', 'yaml_files', '9.yaml')
    parameters = {
        'mp1': 10,
        'wp1': 5.0e-07,
        'lp1': 100.0e-09,
        'mn1': 10,
        'wn1': 5.0e-07,
        'ln1': 100.0e-09,
        'mp3': 10,
        'wp3': 5.0e-07,
        'lp3': 100.0e-09,
        'mn3': 10,
        'wn3': 5.0e-07,
        'ln3': 100.0e-09,
        'mn4': 10,
        'wn4': 5.0e-07,
        'ln4': 100.0e-09,
        'mn5': 10,
        'wn5': 5.0e-07,
        'ln5': 100.0e-09,
        'cap': 5.0e-12,
        'res': 5.0e+3
    }
    process = "TT"
    temp_pvt = 27
    vdd = 1.2
    ngspice_wrapper = NgspiceWrapper(path_yaml)
    
    new_netlist_path = ngspice_wrapper.create_new_netlist(parameters, process, temp_pvt, vdd)
    succeed = ngspice_wrapper.simulate(new_netlist_path)
    print(f"New netlist created at: {new_netlist_path}")
    print("succeed:", succeed)
    print("trf:", ngspice_wrapper.trf)
    print("period:", ngspice_wrapper.period)
    print("VDD:", ngspice_wrapper.VDD)