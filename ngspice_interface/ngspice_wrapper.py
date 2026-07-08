import os
import re
import yaml
import random
import string
import time 
import sys
sys.path.append(".")
from utils import file_utils, sim_utils 
from genai_agent.data import local_config 


_PARAM_ASSIGNMENT_RE = re.compile(r"([A-Za-z_]\w*)\s*=\s*([^\s;]+)")


def _parse_spice_number(value):
    match = re.fullmatch(
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)([A-Za-z]+)?",
        value,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError(f"Unsupported SPICE parameter value: {value}")

    suffix = (match.group(2) or "").lower()
    units = {
        "": 1.0,
        "t": 1e12,
        "g": 1e9,
        "meg": 1e6,
        "k": 1e3,
        "m": 1e-3,
        "u": 1e-6,
        "n": 1e-9,
        "p": 1e-12,
        "f": 1e-15,
    }
    if suffix not in units:
        raise ValueError(f"Unsupported SPICE unit in parameter value: {value}")
    return float(match.group(1)) * units[suffix]


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

            #for dut init
            data_for_dut = yaml_data['dut_config']
            self.is_diff = data_for_dut.get('is_differential')
            self.has_input = data_for_dut.get('has_input')
            self.dc_vout_target = data_for_dut.get('target_dc_vout')
            
        
        

        
    def read_netlist(self):
        with open(self.netlist_path, 'r') as f:
            for line in f:
                if line.startswith(".param"):  # Find parameter lines
                    for param_name, param_value in _PARAM_ASSIGNMENT_RE.findall(line):
                        if param_name in ["trf", "period", "VDD_VAL", "VDD"]:
                            setattr(self, param_name, _parse_spice_number(param_value))
                        elif param_name in self.param_names:
                            self.parameters[param_name] = _parse_spice_number(param_value)

    def generate_random_name(self, length=10):
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters) for _ in range(length))
        timestamp = str(int(time.time()))
        unique_name = timestamp + "_" + random_string
        return unique_name

    def _keep_line_for_analysis_mode(self, line, analysis_mode):
        if analysis_mode == "full":
            return True
        if analysis_mode != "op":
            raise ValueError(f"Unsupported analysis_mode: {analysis_mode}")

        stripped = line.strip().lower()
        if stripped.startswith(("tran ", "ac ", "noise ")):
            return False
        if stripped.startswith("wrdata") and any(token in stripped for token in ("tran_", "ac_", "noise_")):
            return False
        return True

    def create_new_netlist(self, parameters=None, process='TT', temp_pvt=None, vdd=None, vcm=None, vhigh=None, analysis_mode="full"):
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
                param_assignments = _PARAM_ASSIGNMENT_RE.findall(line)
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
                    elif (param_name == "VDD_VAL" or param_name == "VDD") and vdd is not None:
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

        lines = [line for line in lines if self._keep_line_for_analysis_mode(line, analysis_mode)]
        
        # Open the new netlist and write lines
        os.makedirs(os.path.dirname(new_netlist_path), exist_ok=True)
        with open(new_netlist_path, 'w') as output_file:
            output_file.writelines(lines)
        
        return new_netlist_path

    def simulate(self, netlist_path):
        succeed = 0 # this means no error occurred
        nl = file_utils.get_file_to_str(netlist_path)
        # print(netlist_path)
        sim_output = sim_utils.run_ngspice_direct(nl, False, netlist_path)
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
