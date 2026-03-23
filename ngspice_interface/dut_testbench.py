import time
import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.interpolate as interp
import scipy.optimize as sciopt
from scipy.optimize import differential_evolution
from .area_estimation import BPTM45nmAreaEstimator
from .ngspice_wrapper import NgspiceWrapper


class DUT(NgspiceWrapper):
    def measure_metrics(self):
        self.output_files_folder = "./no_backup/output_files"
        self.random_name = "TwoStage"
        self.parse_outputs()
        spec_dict = {}
        # post process raw data
        area_estimator = BPTM45nmAreaEstimator(self.circuit_params, self.circuit_multipliers)
        spec_dict['area'] = area_estimator.find_area()
        # print(f"area: {spec_dict['area']}")
        spec_dict['current'] = self.current
        spec_dict['gain'] = self.find_dc_gain(self.vout_complex)
        spec_dict['noise'] = self.noise
        spec_dict['phm'] = self.find_phm(self.freq, self.vout_complex)
        spec_dict['slewRate'] = self.find_slew_rate(self.time, self.vout_tran, threshold_low=0.1, threshold_high=0.9, time_unit='us')
        spec_dict['ugbw'] = self.find_ugbw(self.freq, self.vout_complex)
        # spec_dict['netV'] = self.netV
        return spec_dict
    
    def parse_outputs(self):
        tran_fname = os.path.join(self.output_files_folder, 'tran_'+self.random_name+'.csv')
        ac_fname = os.path.join(self.output_files_folder, 'ac_'+self.random_name+'.csv')
        dc_fname = os.path.join(self.output_files_folder, 'dc_'+self.random_name+'.csv')
        noise_fname = os.path.join(self.output_files_folder, 'noise_'+self.random_name+'.csv')
        # add these file names in a list
        self.output_files = [tran_fname, ac_fname, dc_fname, noise_fname]
        for file in self.output_files:
            if not os.path.isfile(file):
                print(f"{file} doesn't exist")
        tran_raw_outputs = np.genfromtxt(tran_fname, skip_header=1)
        ac_raw_outputs = np.genfromtxt(ac_fname, skip_header=1)
        dc_raw_outputs = np.genfromtxt(dc_fname, skip_header=1)
        noise_raw_outputs = np.genfromtxt(noise_fname, skip_header=1)

        self.time = tran_raw_outputs[:, 0]
        self.vout_tran = tran_raw_outputs[:, 1]
        
        self.freq = ac_raw_outputs[:, 0]
        vout_real = ac_raw_outputs[:, 1]
        vout_imag = ac_raw_outputs[:, 2]
        self.vout_complex = vout_real + 1j*vout_imag
        
        self.current = - dc_raw_outputs[1]
        self.netV = dc_raw_outputs[[3, 5, 7, 9, 11, 13, 15, 17]]

        # print(f"current: {self.current}")

        self.noise = noise_raw_outputs[0]
        self.noise = np.nan_to_num(self.noise, nan=0.0, posinf=1e6, neginf=-1e6)
        # print(f"noise: {self.noise}")

        # # --- Plotting ---
        # plt.figure(figsize=(12, 5))

        # # Transient plot
        # plt.subplot(1, 2, 1)
        # plt.plot(self.time, self.vout_tran, label='Vout (Tran)')
        # plt.xlabel('Time [s]')
        # plt.ylabel('Voltage [V]')
        # plt.title('Transient Response')
        # plt.grid(True)
        # plt.legend()

        # # AC plot (magnitude in dB)
        # plt.subplot(1, 2, 2)
        # plt.semilogx(self.freq, 20*np.log10(np.abs(self.vout_complex)), label='Vout (AC)')
        # plt.xlabel('Frequency [Hz]')
        # plt.ylabel('Magnitude [V/V]')
        # plt.title('AC Response')
        # plt.grid(True, which='both', linestyle='--')
        # plt.legend()

        # plt.tight_layout()
        # plt.show()
    
    def find_dc_gain(self, vout):
        """
        TODO: Implement the DC gain calculation
        
        Hint:
        Use numpy's abs() function to calculate the magnitude of the complex number at each point.
        """
        # pass
        dc_gain = np.abs(self.vout_complex[0])
        # print(f"dc_gain: {dc_gain}\n")
        return dc_gain
        
        
    def find_ugbw(self, freq, vout):
        """
        TODO: Implement the unity gain bandwidth (UGBW) calculation
        
        Hints:
        1. Calculate the magnitude of vout
        2. Find where the magnitude crosses 1 (unity gain)
        3. Use _get_best_crossing() to find the crossing point through interpolation
        4. What should you if no crossing is found? What situations can lead to this?
        """
        # pass
        ac_mag = np.abs(self.vout_complex)
        ac_cross, ac_found = self._get_best_crossing(self.freq,ac_mag,1)
        if not ac_found:
            return 0
        # print(f"ugbw: {ac_cross}\n")
        return ac_cross

    
    def find_phm(self, freq, vout):
        """
        TODO: Implement the phase margin (PHM) calculation
        
        Hints:
        1. Calculate gain array and phase array from vout
        2. Find the unity gain frequency (UGBW)
        3. Interpolate to find the phase at UGBW (you can use interp.interp1d quadratic interpolation)
        4. Calculate phase margin (watch out for radians/degrees units and phase wrap around)
        5. Handle edge cases (e.g., when gain is always < 1) --> hint: you can think in RL terms; worst case reward ...
        """
        # pass
        gain = self.find_dc_gain(vout) # or use self? idk, if bug fix here
        ugbw = self.find_ugbw(self.freq,self.vout_complex)
        if ugbw <= np.min(self.freq) or ugbw >= np.max(self.freq) or ugbw == 0:
            print("Warning: UGBW out of interpolation range or not found")
            return 0
        phi_deg = np.unwrap(np.angle(self.vout_complex))*180/np.pi
        phi_interpolate = interp.interp1d(self.freq,phi_deg)
        phi_ugbw = phi_interpolate(ugbw)

        phm = 180 + phi_ugbw
        # print(f"phm: {phm}\n")
        
        return phm
    
    def find_slew_rate(self, time, signal, threshold_low=0.1, threshold_high=0.9, time_unit='us'):
        """
        TODO: Implement the slew rate calculation
        
        Hints:
        1. Find large rising edges in the signal
        2. Calculate slope for each rising edge
        3. Take the average of these slopes
        5. Handle edge cases (e.g., no rising edges found)
        6. Final value should be in V/us
        """
        # pass
        vmin = np.min(self.vout_tran)
        vmax = np.max(self.vout_tran)

        vlo = vmin + threshold_low*(vmax-vmin)
        vhi = vmin + threshold_high*(vmax-vmin)

        slew_ary = []
        for i in range(4,len(self.vout_tran)-4):
            if self.vout_tran[i-1] < vlo <= self.vout_tran[i]:
                for j in range(i, len(self.vout_tran)-4):   # cam i use pointers in python??? check later for higher search efficiency
                    if self.vout_tran[j-1] < vhi <= self.vout_tran[j]:
                        t_r1, found_r1 = self._get_best_crossing(time[i-4:j+4], signal[i-4:j+4], vlo)
                        t_r2, found_r2 = self._get_best_crossing(time[i-4:j+4], signal[i-4:j+4], vhi)
                        if found_r1 and found_r2: #
                            slew_ary.append((vhi - vlo) / (t_r2 - t_r1))
                            i=j
                        break
        if not slew_ary:
            print("Warning: Not Slew Rate")
            return 0
        mean = np.mean(slew_ary)*1e-6
        # print(f"slew: {mean}\n")
        return mean


        

    def _get_best_crossing(cls, xvec, yvec, val):
        interp_fun = interp.InterpolatedUnivariateSpline(xvec, yvec)

        def fzero(x):
            return interp_fun(x) - val

        xstart, xstop = xvec[0], xvec[-1]
        try:
            return sciopt.brentq(fzero, xstart, xstop), True
        except ValueError:
            return xstop, False

#  make a main to run this

# if __name__ == "__main__":
#     project_path = os.getcwd()
#     yaml_path = os.path.join(project_path, 'ngspice_interface', 'files', 'yaml_files', 'TwoStage.yaml')
#     parameters = {
#         'mp1': 10,
#         'wp1': 5.0e-07,
#         'lp1': 100.0e-09,
#         'mn1': 10,
#         'wn1': 5.0e-07,
#         'ln1': 100.0e-09,
#         'mp3': 10,
#         'wp3': 5.0e-07,
#         'lp3': 100.0e-09,
#         'mn3': 10,
#         'wn3': 5.0e-07,
#         'ln3': 100.0e-09,
#         'mn4': 10,
#         'wn4': 5.0e-07,
#         'ln4': 100.0e-09,
#         'mn5': 10,
#         'wn5': 5.0e-07,
#         'ln5': 100.0e-09,
#         'cap': 5.0e-12,
#         'res': 5.0e+3
#     }
#     process = "TT"
#     temp_pvt = 27
#     vdd = 1.2
#     dut_tb = DUT(yaml_path)

#     dut_tb.output_files_folder = "./no_backup/output_files"
#     dut_tb.random_name = "TwoStage"
    
#     new_netlist_path = dut_tb.create_new_netlist(parameters, process, temp_pvt, vdd)
#     info = dut_tb.simulate(new_netlist_path)
#     dut_tb.random_name = "TwoStage"
#     print(f"New netlist created at: {new_netlist_path}")
#     print("info:", info)
#     print("trf:", dut_tb.trf)
#     print("period:", dut_tb.period)
#     print("VDD:", dut_tb.VDD)
#     dut_tb.measure_metrics()