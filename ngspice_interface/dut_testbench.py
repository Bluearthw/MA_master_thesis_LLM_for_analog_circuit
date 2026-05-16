import time
import re
import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.interpolate as interp
import scipy.optimize as sciopt
from scipy.optimize import differential_evolution

from .area_estimation import BPTM45nmAreaEstimator
from .ngspice_wrapper import NgspiceWrapper
# from area_estimation import BPTM45nmAreaEstimator
# from ngspice_wrapper import NgspiceWrapper
import sys
from scipy.integrate import trapezoid
sys.path.append(".")
from genai_agent.local_config import table_target_id 
from utils import gen_utils
class DUT(NgspiceWrapper):
    def __init__(self, path_yaml = "", is_differential = False, has_input = True, dc_vout_target = None, netlist_path = None):
        super().__init__(path_yaml)
        if path_yaml == "": # these are also from yaml
            self.is_diff = is_differential
            self.has_input = has_input
            self.dc_vout_target = dc_vout_target
            self.netlist_path = netlist_path
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
        # type23
        self.sink_path = None
        self.source_path = None
        self.mismatch = None
        self.compliance_range_min_max = None

        self.vdd = None
        

    def measure_metrics(self, struct_path_id, is_init = True):
        self.output_files_folder = "./no_backup/output_files"
        if is_init:
            self.random_name = self.circuit_name # this is for intermediate cir file for RL sizing
        # self.parse_outputs()
        spec_dict = {}
        # post process raw data
        if self.with_yaml:
            area_estimator = BPTM45nmAreaEstimator(self.circuit_params, self.circuit_multipliers)
            spec_dict['area'] = area_estimator.find_area()


        for spec_id, path in struct_path_id.items():
            # print(spec_id)
            if spec_id == 0:  # DC gain 
                a = self.get_dc_gain(path)
                # print(f"DC gain: {a}")
                name = table_target_id[0]# you should not use '0' but 0 since the key is int
                spec_dict[name] = float(a) # this is the magnitude you do not the whether it is inverted.
            elif spec_id == 1:  # Bandwidth (if separate from gain) or other AC sim
                spec_dict[table_target_id[1]] = float(self.get_bandwidth(path))
            
            elif spec_id == 2:  # PSRR
                spec_dict[table_target_id[2]] = self.get_psrr(path, self.has_input)[0] #[1] is freq
            
            elif spec_id == 3:  # input noise
                spec_dict[table_target_id[3]] = float(self.get_in_equivalent_total_noise(path))
            #Trans
            elif spec_id == 4:  # slew rate
                spec_dict[table_target_id[4]] = float(self.get_slew_rate(path))
            
            elif spec_id == 5:  # gain margin
                spec_dict[table_target_id[5]] = float(self.get_gain_margin(path)) 
            elif spec_id == 6:  # phase margin
                spec_dict[table_target_id[6]] = float(self.get_phase_margin(path))
            elif spec_id == 7:  # input equivalent total noise from spectrum
                spec_dict[table_target_id[7]] = self.get_in_equivalent_total_noise(path)
            
            elif spec_id == 10:
                spec_dict[table_target_id[10]] = 0# to be done
            
            elif spec_id == 11:  # outputswing, it is a tuple(vrange, v_min, v_max)
                spec_dict[table_target_id[11]] = self.get_output_swing(path)[0]
            
            elif spec_id == 12:  # settle time
                spec_dict[table_target_id[12]] = float(self.get_settle_time(path))
            
            elif spec_id == 13:  # icmr, it is a tuple(vrange, vcm, v_min, v_max)
                spec_dict[table_target_id[13]] = self.get_icmr(path)[0]

            elif spec_id == 14:  # cmrr, it is a list
                spec_dict[table_target_id[14]] = self.get_cmrr(path)[0]

            elif spec_id == 15:
                spec_dict[table_target_id[15]] = self.get_ac_gain(path)

            elif spec_id == 16:  # gain margin
                spec_dict[table_target_id[16]] = self.get_phase_response(path)# it is an list
            
            elif spec_id == 17:
                spec_dict[table_target_id[17]] = self.get_common_mode_gain(path)
            elif spec_id == 18:
                spec_dict[table_target_id[18]] = self.get_differential_mode_gain(path)
            elif spec_id == 19:
                spec_dict[table_target_id[19]] = self.get_output_balance(path)
            elif spec_id == 20:
                spec_dict[table_target_id[20]] = self.get_cmfb_stb(path)
            elif spec_id == 21:
                spec_dict[table_target_id[21]] = self.get_ugbw_unity_gain_bandwidth(path)
            elif spec_id == 22:
                spec_dict[table_target_id[22]] = self.get_current(path) 
            elif spec_id == 23:
                if self.dc_vout_target is None:
                    raise ValueError("Target DC output voltage is not specified")
                spec_dict[table_target_id[23]] = self.get_dc_vout_relative_err(path, dc_vout_target= self.dc_vout_target) 
                print("dut:", spec_dict[table_target_id[23]])
                # spec_dict[table_target_id[23]+"_target_vout"] = self.get_dc_vout(path) 
            elif spec_id == 24:
                spec_dict[table_target_id[24]] = self.get_line_regulation(path) 
            elif spec_id == 25:
                spec_dict[table_target_id[25]] = self.get_load_regulation(path) 
            elif spec_id == 26:
                spec_dict[table_target_id[26]] = self.get_temperature_coefficient(path) 
            elif spec_id == 27:
                spec_dict[table_target_id[27]] = self.get_startup_behavior(path) 
            elif spec_id == 28:
                spec_dict[table_target_id[28]] = self.get_current_matching(path) 
            elif spec_id == 29:
                vout_ripple = self.get_output_ripple(path) 
                
                spec_dict[table_target_id[29]] = vout_ripple
            elif spec_id == 30:
                spec_dict[table_target_id[30]] = self.get_voltage_compliance_range(path)
            else:
                continue
        print(spec_dict)
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
    

    def get_current(self, path_i =""):
        if path_i == "" and self.current is not None:
            return self.current
        elif path_i != "":
            data_op = np.genfromtxt(path_i, autostrip=True, skip_header=1)

            current = abs(data_op[1]) # if op is used, the first col is always vout
            self.current = current
            return current
        else:
            raise ValueError("Current data not available and no path provided")
        

    def load_ac_gain_data(self, path_gain=""):
        if self.is_diff == False:
            self.path_ac_gain = path_gain
            data_gain = np.genfromtxt(path_gain, autostrip=True, skip_header=1)
            self.freq = data_gain[:, 0]
            # store gain as complex and compute magnitude/phase
            # self.vout_complex = data_gain[:, 1] + 1j * data_gain[:, 2]
            self.vout_complex = self._complex_from_cols(data_gain, 1, 2)
            self.vout_mag_db = np.abs(self.vout_complex)
            self.mag_db = 20 * np.log10(self.vout_mag_db)
            phase = np.unwrap(np.angle(self.vout_complex, deg=True), period=360)
            if np.average(phase) > 0 and phase[0] > 175:
                self.phase = phase - 180
            else:
                self.phase = phase
        else:
            raise ("why dif goes to load_ac_gain_data()")
    
    def load_adm_data(self, path_adm = ""):
        self.path_adm = path_adm
        # ADM files can have repeated frequency columns (one per output) and may include header.
        # Expected layout (based on sample):
        # frequency  v(VOUT1)  v(VOUT1)  frequency  v(VOUT2)  v(VOUT2)
        # (freq, real1, imag1, freq, real2, imag2)
        print("path_adm : ",path_adm)
        data_adm = np.genfromtxt(path_adm, autostrip=True, skip_header=1)
        # if it is still 1 col
        if data_adm.ndim == 1:
            data_adm = data_adm.reshape(1, -1)

        self.freq = data_adm[:, 0]
        self.vout1_complex = self._complex_from_cols(data_adm, 1, 2)
        self.vout2_complex = self._complex_from_cols(data_adm, 4, 5)

        self.phase_v1 = np.unwrap(np.angle(self.vout1_complex, deg=True), period=360)
        self.phase_v2 = np.unwrap(np.angle(self.vout2_complex, deg=True), period=360)

        self.vout_complex = self.vout1_complex - self.vout2_complex
        self.vout_mag_db = np.abs(self.vout_complex)
        self.mag_db = 20 * np.log10(self.vout_mag_db)
        self.phase = np.unwrap(np.angle(self.vout_complex, deg=True), period=360)

    #0 DC Gain
    def get_dc_gain(self, path_gain="", ):
        """Returns the magnitude at the lowest frequency."""
        if self.path_ac_gain is None and not self.is_diff :
            self.load_ac_gain_data(path_gain)
        elif self.path_adm is None and self.is_diff:
            self.load_adm_data(path_gain)

        return self.vout_mag_db[0]

    #1 Bandwidth
    def get_bandwidth(self,path=""):
        """Finds the -3dB cutoff frequency."""
        if self.is_diff:
            if self.path_adm is None:
                self.load_adm_data(path)
        else:
            if self.path_ac_gain is None:
                self.load_ac_gain_data(path)
        #used for both, it is already 1 signal after calculation
        length = len(self.mag_db)
        last_mag_db =  np.mean(self.mag_db[int(length*0.7) : -1])
        first_mag_db = np.mean(self.mag_db[0 : int(length*0.3)])
        if last_mag_db < first_mag_db: 
        # LP
            target = self.mag_db[0] - 3
            bw, found = self._get_best_crossing(self.freq, self.mag_db, target)
            return bw if found else 0
        else:#HP
            target = self.mag_db[-1] - 3
            bw, found = self._get_best_crossing(self.freq, self.mag_db, target)
            return self.freq[-1] - bw if found else 0

    #15 AC gain #single port
    def get_ac_gain(self, path_gain=""):
        """Returns the maximum gain in dB."""
        if self.path_ac_gain is None:
            self.load_ac_gain_data(path_gain)
        return self.mag_db
    
    #17 common-mode gain (Vout1+Vout2)/2
    def get_common_mode_gain(self, path_adm=""):
        """Return the common-mode gain (dB) based on the adm file."""
        if self.path_adm is None:
            self.load_adm_data(path_adm)

        v_common = (self.vout1_complex + self.vout2_complex) / 2
        mag = np.abs(v_common)
        return mag, 20 * np.log10(mag)

    #18 differential-mode gain (Vout1 - Vout2)
    def get_differential_mode_gain(self, path_adm=""):
        """Return the differential-mode gain (dB) based on the adm file."""
        if self.path_adm is None:
            self.load_adm_data(path_adm)
        return self.vout_mag_db, self.mag_db
        
    #16 phase response
    def get_phase_response(self, path_gain=""):
        """Returns the phase response array."""
        if self.path_ac_gain is None:
            self.load_ac_gain_data(path_gain)
        return self.phase

    #5 gain margin
    def get_gain_margin(self, path_gain):
        """
        Calculates the gain margin (in dB).
        Gain margin is the gain at the phase crossover frequency (where phase = -180°).
        """
        if self.path_ac_gain is None:
            self.load_ac_gain_data(path_gain)
        phi_deg = self.phase
        
        # print(phi_deg[-1])
        # print(phi_deg[0])
        if phi_deg[0] < 1 :
            target_phase = -180
        else:
            target_phase = 0
        
        try:
            phi_interpolate = interp.interp1d(self.freq, phi_deg)
            mag_db_interpolate = interp.interp1d(self.freq, self.mag_db)
            
            def phase_error(f):
                return phi_interpolate(f) - target_phase
            
            # Find the crossing frequency where phase = -180°
            xstart, xstop = self.freq[0], self.freq[-1]
            phase_crossover_freq = sciopt.brentq(phase_error, xstart, xstop)
            
            # Get the gain at the phase crossover frequency
            gain_at_crossing = mag_db_interpolate(phase_crossover_freq)
            
            # Gain margin is -gain (in dB) at the phase crossover frequency
            # Positive gain margin means stable system
            gain_margin = -gain_at_crossing
            
            return gain_margin
        except ValueError:
            # Phase never crosses -180 degrees
            print("Warning: Phase does not cross -180 degrees in the frequency range")
            if (phi_deg[-1] < 10 and phi_deg[0] > 1) or (phi_deg[-1] < -170 and phi_deg[0] < 1):
                return self.freq[-1]
            else:
                return 0

    #6 phase margin # assumed LP!!!
    def get_phase_margin(self, path_gain=""): 
        if self.is_diff:
            if self.path_adm is None:
                self.load_adm_data(path_gain)
        else:
            if self.path_ac_gain is None or self.phase is None:
                self.load_ac_gain_data(path_gain)
            
        ugbw = self.get_ugbw_unity_gain_bandwidth()
        print("ugbw",ugbw)
        if ugbw <= np.min(self.freq) or ugbw >= np.max(self.freq) or ugbw == 0:
            print("Warning: UGBW out of interpolation range or not found yet")
            return 0
        phi_deg = self.phase
        phi_interpolate = interp.interp1d(self.freq,phi_deg)
        phi_ugbw = phi_interpolate(ugbw)

        phm = 180 + phi_ugbw
        print(f"phm: {phm}\n")
        
        return phm
    
    #19 output balance
    def get_output_balance(self,path, error_deg = 5):
        if len(self.phase_v1) and len(self.phase_v2):
            self.load_adm_data(path)
        diffs = np.abs(self.phase_v1 - self.phase_v2) % 360
        return np.all(np.abs(diffs - 180) <= error_deg)
    
    #20 cmfb stb
    def get_cmfb_stb(self, path_cmfb_stb):
        """Analyze CMFB loop stability from simulation data.
        
        Args:
            path_cmfb_stb: Path to the CMFB stability CSV file with columns:
                          freq, v(in) real, v(in) imag, freq, v(out) real, v(out) imag
        
        Returns:
            tuple: (is_stable: bool, phase_margin: float, gain_margin: float)
        """
        data = np.genfromtxt(path_cmfb_stb, skip_header=1)
        
        freq = data[:, 0]
        v_in_real = data[:, 1]
        v_in_imag = data[:, 2]
        v_out_real = data[:, 4]
        v_out_imag = data[:, 5]
        
        v_in = v_in_real + 1j * v_in_imag
        v_out = v_out_real + 1j * v_out_imag
        
        # Loop gain = v_out / v_in
        loop_gain = v_out / v_in
        mag_db = 20 * np.log10(np.abs(loop_gain))
        phase_deg = np.unwrap(np.angle(loop_gain, deg=True), period=360)
        
        # Phase margin: phase at gain = 0dB
        try:
            pm_cross_freq, pm_found = self._get_best_crossing(freq, mag_db, 0)
            if pm_found:
                phase_at_0db = np.interp(pm_cross_freq, freq, phase_deg)
                phase_margin = 180 + phase_at_0db
            else:
                phase_margin = float('inf') if np.all(mag_db > 0) else float('-inf')
        except:
            phase_margin = 0
        
        # Gain margin: gain at phase = -180°
        try:
            def phase_error(f):
                return np.interp(f, freq, phase_deg) - (-180)
            
            xstart, xstop = freq[0], freq[-1]
            phase_cross_freq = sciopt.brentq(phase_error, xstart, xstop)
            gain_at_180deg = np.interp(phase_cross_freq, freq, mag_db)
            gain_margin = -gain_at_180deg
        except ValueError:
            # Phase never crosses -180°
            gain_margin = float('inf') if np.all(phase_deg > -180) else float('-inf')
        
        # Stable if both margins are positive
        is_stable = gain_margin > 0 and phase_margin > 0
        
        return is_stable, phase_margin, gain_margin

    #3 input equivalent integrated total noise
    def get_in_equivalent_total_noise(self, path): # there is another vector that might calculate the integrated noise, 
        
        data_noise = np.genfromtxt(path, autostrip=True, skip_header=1)
        # this is total so just skip output, and head is skipped.
        if np.size(data_noise) > 50:
            return self.get_in_equivalent_total_noise_from_spectrum(path)
        else:
            return data_noise[1] 

    #7 input equivalent noise spectrum
    def get_in_equivalent_total_noise_from_spectrum(self, path): # there is another vector that might calculate the integrated noise, 
        data_noise = np.genfromtxt(path, autostrip=True, skip_header=1)
        #0,2 are f, 1 is onoise, 3 is inoise
        inoise = data_noise[:, 1] 
        # 2. Square the noise to get V^2/Hz (Power Density)
        noise_power_density = inoise**2
        
        # 3. Integrate over frequency
        f_range = data_noise[:, 0] # frequency range
        total_variance = trapezoid(noise_power_density, f_range)
        
        # 4. Take the square root to get back to RMS Volts
        return np.sqrt(total_variance)

    #8 input impedance
    def get_input_impedance(self):
        # TODO: Implement input impedance calculation
        # Requires additional simulation data (e.g., input current vs voltage)
        return 0

    #9 output impedance
    def get_output_impedance(self):
        # TODO: Implement output impedance calculation
        # Requires additional simulation data
        return 0

    #4 slew rate
    def get_slew_rate(self, path, threshold_low=0.1, threshold_high=0.9, time_unit='us'): # there is another vector that might calculate the integrated noise, 
        if self.path_trans is None:
            self.path_trans = path
            data_trans = np.genfromtxt(path, autostrip=True, skip_header=1)
            self.data_trans = data_trans
        vout_tran = self.data_trans[:, 1] #  vout is the second column
        time = self.data_trans[:, 0] #  time is the first column

        vmin = np.min(vout_tran)
        vmax = np.max(vout_tran)
        # print(f"vmin: {vmin}, vmax: {vmax}")
        vlo = vmin + threshold_low*(vmax-vmin)
        vhi = vmin + threshold_high*(vmax-vmin)

        slew_ary = []
        for i in range(4,len(vout_tran)-4):
            if vout_tran[i-1] < vlo <= vout_tran[i]:
                for j in range(i, len(vout_tran)-4):   # cam i use pointers in python??? check later for higher search efficiency
                    if vout_tran[j-1] < vhi <= vout_tran[j]:
                        # print("time range",time[i-4:j+4])
                        t_r1, found_r1 = self._get_best_crossing(time[i-4:j+4], vout_tran[i-4:j+4], vlo)
                        t_r2, found_r2 = self._get_best_crossing(time[i-4:j+4], vout_tran[i-4:j+4], vhi)
                        if found_r1 and found_r2: #
                            slew_ary.append((vhi - vlo) / (t_r2 - t_r1))
                            i=j
                        break
        if not slew_ary:
            print("Warning: Not Slew Rate")
            return 0
        mean = np.mean(slew_ary)*1e-6
        return mean

    #12 settle time
    def get_settle_time(self, path, error_margin=0.01):
        # TODO: Implement settle time calculation
        if self.path_trans is None:
            self.path_trans = path
            data_trans = np.genfromtxt(path, autostrip=True, skip_header=1)
            self.data_trans = data_trans
        if self.is_diff:
            time = self.data_trans[:,0]
            v1 = self.data_trans[:,1]
            v2 = self.data_trans[:,3]
            v_diff = v1 - v2
    
            # 2. Determine Steady State (Final Value)
            final_value = np.mean(v_diff[-int(len(v_diff)*0.05):])
            
            # 3. Define the Error Band
            error_band = abs(final_value * error_margin)
            upper_bound = final_value + error_band
            lower_bound = final_value - error_band
            
            # We look for indices where the signal is OUTSIDE the band
            outside_indices = np.where((v_diff > upper_bound) | (v_diff < lower_bound))[0]
            
            if len(outside_indices) == 0:
                return 0.0  # Already settled
            
            # The last index where it was "outside" + 1 is the point it "settled"
            last_outside_idx = outside_indices[-1]
            
            # Ensure we don't exceed array bounds
            settle_idx = min(last_outside_idx + 1, len(time) - 1)
            
            settle_time_absolute = time[settle_idx]
            
            # Settling time is relative to when the pulse started
            return settle_time_absolute
        return 0

    #10 Input swing
    def get_input_swing(self):
        # TODO: Implement input swing calculation
        # Requires DC sweep data
        return 0

    #11 Output swing
    def get_output_swing(self, path, error = 0.05):
        data = np.genfromtxt(path, autostrip=True, skip_header=1)
        v_in = data[:,0]
        v_out = data[:,1]
        gain = np.abs(np.gradient(v_out, v_in)) 
        max_gain = np.max(gain)
        
        # 2. Find indices where gain is at least 50% of max (for example)
        valid_indices = np.where(gain >= max_gain * (1-error))[0]
        
        # 3. Get the output voltages at these "edge" indices
        out_swing_min = v_out[valid_indices[-1]] # Usually lower Vout
        out_swing_max = v_out[valid_indices[0]]  # Usually higher Vout
        
        useful_swing_range = out_swing_max - out_swing_min
        return useful_swing_range, out_swing_min, out_swing_max

    #2 Power Supply Rejection Ratio (PSRR)
    def get_psrr(self, path_psrr, has_input): # maybe it can be interpolated to get more precise value
        """Return arrays (frequency, psrr_db) from the parsed PSRR file."""
        if self.path_psrr is None:
            self.path_psrr = path_psrr
        data_psrr = np.genfromtxt(path_psrr, autostrip=True, skip_header=1)
        psrr_gain_complex = data_psrr[:, 1] + 1j * data_psrr[:, 2]
        psrr_gain_mag = np.abs(psrr_gain_complex)
        psrr_gain_mag_db = 20 * np.log10(psrr_gain_mag)
        freq = data_psrr[:, 0]
        if has_input:
            len_psrr = len(data_psrr[:, 0])
            len_gain = len(self.vout_mag_db)
            if len_psrr < len_gain:
                psrr_db = self.vout_mag_db[0: len_psrr] - psrr_gain_mag_db # should use subtraction since they are  dB
            else: #psrr >= ac gain
                psrr_db = self.vout_mag_db - psrr_gain_mag_db[0: len_gain]
                freq = self.freq
        else:
            psrr_db = 0 - psrr_gain_mag_db
        
        return psrr_db, freq
    
    #13 Input Common-Mode Range (ICMR)
    def get_icmr(self, path_icmr, error = 0.05): # Input Common-Mode Range
        data = np.genfromtxt(path_icmr, autostrip=True, skip_header=1)
        v_sweep = data[:,0]
        vout = data[:,1]
        gain = np.abs(np.gradient(vout, v_sweep))
        # print("==imcr gain",gain)

        
        max_gain = np.max(gain) # Find the maximum gain, should be VCM
        print(max_gain)
        # Find indices where gain is at least 99% of max_gain
        # (This is your 1% error margin)
        logic_test = (gain >= (1-error) * max_gain)
        valid_indices = np.where(logic_test)[0]
        
        if len(valid_indices) > 0:
            v_min = v_sweep[valid_indices[0]] # the voltage is increasing
            v_max = v_sweep[valid_indices[-1]]
            vcm = (v_max+ v_min)/2
            vrange = v_max-v_min
            return vrange, vcm, v_min, v_max
        return None, None, None, None

    #14 Common-Mode Rejection Ratio (CMRR)
    def get_cmrr(self, path_acm):
        data_cm = np.genfromtxt(path_acm, skip_header=1)
        # Column 0: Freq, Column 1: Real, Column 2: Imag (or Mag depending on wrdata)
        # If using default wrdata, it's usually Real/Imag pairs
        if self.mag_db is None:
            raise ValueError("there is no ac_dm when you want cmrr!!")

        adm_mag = self.vout_mag_db

        vcm_complex = data_cm[:, 1] + 1j * data_cm[:, 2]
        acm_mag = np.abs(vcm_complex)

        len_dm = len(adm_mag)
        len_cm = len(acm_mag)
        if len_dm < len_cm:
            cmrr = adm_mag / acm_mag[0: len_dm]
            freq = data_cm[:, 0]
        else: #psrr >= ac gain
            cmrr = adm_mag[0: len_cm] / acm_mag
            freq = self.freq

        cmrr_db = 20 * np.log10(cmrr)
        return  cmrr_db, freq # Return freq and CMRR in dB

    def get_dc_vout_relative_err(self, path, dc_vout_target=0.1):
        """Return the relative DC output voltage from a DC measurement file."""
        data = np.genfromtxt(path, autostrip=True, skip_header=1)
        if data.size == 0:
            data = np.genfromtxt(path, autostrip=True, skip_header=0) # sometimes no header
            if data.size == 0:
                raise ValueError(f"No data found in DC output file: {path}")
            
        if data.ndim == 1:
            vout = float(data[1] if data.shape[0] > 1 else data[0])
            return abs((vout - dc_vout_target) / dc_vout_target)
        if data.shape[1] == 1:
            return float(data[-1, 0])
        raise ValueError(f"Unexpected data format in DC output file: {path}")

    def get_line_regulation(self, path):
        """Compute line regulation in (V/V) % from a VDD sweep file."""
        data = np.genfromtxt(path, autostrip=True, skip_header=1)
        if data.ndim == 1 or data.shape[0] < 2:
            return 0.0
        vdd = data[:, 0]
        vout = data[:, 1]
        delta_vdd = np.max(vdd) - np.min(vdd)
        delta_vout = np.max(vout) - np.min(vout)
        if delta_vdd == 0:
            return 0.0
        # print(delta_vdd)
        # print(delta_vout)
        return abs(delta_vout / delta_vdd) * 100.0

    def get_load_regulation(self, path):
        """Compute load regulation in mV/mA from a load current sweep file."""
        data = np.genfromtxt(path, autostrip=True, skip_header=1)
        if data.ndim == 1 or data.shape[0] < 2:
            return 0.0
        i_load = data[:, 0]
        vout = data[:, 1]
        delta_i = i_load[-1] - i_load[0]
        delta_vout = vout[-1] - vout[0] # no load V and max load V. It is not min max V
        if delta_i == 0:
            return 0.0
        # vout 0 is the no load vout (open, i = 0)
        return abs(delta_vout / vout[-1]) * 100.0

    def get_temperature_coefficient(self, path, ref_temp=27.0):
        """Compute temperature coefficient in ppm/°C from a temperature sweep file."""
        data = np.genfromtxt(path, autostrip=True, skip_header=1)
        if data.ndim == 1 or data.shape[0] < 2:
            return 0.0
        temp = data[:, 0]
        vout = data[:, 1]
        delta_temp = temp[-1] - temp[0]
        if delta_temp == 0:
            return 0.0
        # Use the output voltage at 27°C as the reference voltage (Vref)
        nearest_index = np.argmin(np.abs(temp - ref_temp))
        vref = float(vout[nearest_index])
        if vref == 0:
            return 0.0
        delta_vout = np.max(vout) - np.min(vout)  # ✅ Full voltage range

        return abs(delta_vout / vref / delta_temp) * 1e6 #1e6 is for ppm

    def get_startup_behavior(self, path, goal_percentage=0.9):
        """Estimate startup behavior as the time to reach 90% of final output."""
        data = np.genfromtxt(path, autostrip=True, skip_header=1)
        if data.ndim == 1 or data.shape[0] < 2:
            return 0.0
        time_data = data[:, 0]
        vout = data[:, 1]
        final_value = np.mean(vout[-max(1, int(len(vout) * 0.1)):])
        if final_value == 0:
            return float(time_data[-1])
        threshold = final_value * goal_percentage
        if final_value > 0:
            indices = np.where(vout >= threshold)[0]
        else:
            indices = np.where(vout <= threshold)[0]
        return float(time_data[indices[0]]) if indices.size else float(time_data[-1])

    # Helper methods
    def get_ugbw_unity_gain_bandwidth(self, path = ""):
        """Finds the frequency where gain is 0dB."""
        if self.is_diff:
            if self.path_adm is None:
                self.load_adm_data(path)
        else:
            if self.path_ac_gain is None:
                self.load_ac_gain_data(path)
        # print("ugbw:",
        # self.mag_db[0],
        # self.mag_db[-1],
        # max(self.mag_db),
        # min(self.mag_db))

        ugbw, found = self._get_best_crossing(self.freq, self.mag_db, 0)
        return ugbw if found else 0
        
    def get_current_matching(self, paths):
        """Compute current matching as max absolute difference between source and sink currents in A."""
        if len(paths) != 2:
            raise ValueError("Expected exactly two paths for current matching.")
        for path in paths:
            if 'source' in path:
                self.source_path = path
            elif 'sink' in path:
                self.sink_path = path
        if self.compliance_range_min_max is None:
            self.get_voltage_compliance_range(paths) # also mismatch calculation
        if self.compliance_range_min_max is None:
            return 100
        mismatch_percentage = (self.mismatch) * 100
        if self.is_interpolate:
            raise ValueError("Interpolation is not supported for current matching.")
        else:

            idx_start, idx_end = self.compliance_range_min_max[2], self.compliance_range_min_max[3]
        # print(idx_start, idx_end)
        if idx_start == idx_end:
            return 100
        mismatch_percentage = mismatch_percentage[idx_start:idx_end]
        # print(mismatch_percentage)
        return np.max(mismatch_percentage) # max only looks for those are true

    def get_output_ripple(self, path, steady_state_ratio=0.5):
        """Compute output ripple in V from a ripple sweep file."""
        try:
        # Some SPICE outputs use commas or tabs; default to autodetecting whitespace
            data = np.genfromtxt(path, autostrip=True)
        except Exception:
            return 0.0
        if data.size == 0 or data.ndim < 2 or data.shape[0] < 10:
            return 0.0

        # Extract time and voltage columns
        # wrdata outputs: [time, v(VCONT1)]
        time = data[:, 0]
        vout = data[:, 1]
        total_points = len(time)
        start_idx = int(total_points * (1 - steady_state_ratio))

        steady_state_vout = vout[start_idx:]

        if len(steady_state_vout) == 0:
            return 0.0

        # 2. Calculate Peak-to-Peak Ripple
        # Tip: If your simulation has high-frequency numerical noise,
        # you could use np.percentile(steady_state_vout, 99.9) - np.percentile(steady_state_vout, 0.1)
        # to reject single-point solver glitch spikes.
        ripple = np.max(steady_state_vout) - np.min(steady_state_vout)

        return float(ripple)

    def get_voltage_compliance_range(self, paths, error = 0.05):
        """Compute voltage compliance in V from a compliance sweep file."""
        if self.source_path is None or self.sink_path is None:
            if len(paths) != 2:
                raise ValueError("Expected exactly two paths for voltage compliance.")
            for path in paths:
                if 'source' in path.lower():
                    self.source_path = path
                elif 'sink' in path.lower():
                    self.sink_path = path
            if self.source_path is None or self.sink_path is None:
                raise ValueError("Could not identify source and sink paths for voltage compliance.")

        data_sink = np.genfromtxt(self.sink_path, autostrip=True, skip_header=1)
        data_source = np.genfromtxt(self.source_path, autostrip=True, skip_header=1)
        if data_sink.ndim == 1 or data_sink.shape[0] < 2 or data_source.ndim == 1 or data_source.shape[0] < 2:
            return 0.0

        v_sink = data_sink[:, 0]
        v_source = data_source[:, 0]
        i_sink = data_sink[:, 1]
        i_source = data_source[:, 1]

        if not np.allclose(v_sink, v_source):
            # Align both current sweeps to the same voltage points using interpolation.
            common_v = np.intersect1d(v_sink, v_source)
            if common_v.size == 0:
                common_v = np.linspace(max(v_sink.min(), v_source.min()), min(v_sink.max(), v_source.max()), min(len(v_sink), len(v_source)))
            i_sink = np.interp(common_v, v_sink, i_sink)
            i_source = np.interp(common_v, v_source, i_source)
            v_sweep = common_v
            self.is_interpolate = True
        else:
            v_sweep = v_source
            self.is_interpolate = False

        i_sink_abs = np.abs(i_sink)
        i_source_abs = np.abs(i_source)


        i_avg = (i_source_abs + i_sink_abs) / 2.0
        i_avg = np.where(i_avg == 0, 1e-12, i_avg)
        mismatch = np.abs(i_source_abs - i_sink_abs) / i_avg
        self.mismatch = mismatch

        if self.vdd is None:
            self.vdd = self.get_vdd()
        vdd = self.vdd
        if vdd is not None and vdd > 0:
            v_sweep = np.clip(v_sweep, 0.0, vdd)
        else:
            raise ValueError("Invalid VDD value.")

        valid = mismatch <= error
        if not np.any(valid):
            return 0.0

        # Find the longest contiguous compliance region.
        # print(valid)
        best_start = best_end = None
        current_start = 0
        for idx in range(1, len(valid)):
            if valid[idx - 1] and not valid[idx]: # true to false down slope
                if best_start is None or (idx - 1 - current_start) > (best_end - best_start):
                    best_start, best_end = current_start, idx - 1
            if not valid[idx]: # last false
                current_start = idx + 1
        if valid[-1]: # if last is true ????
            if best_start is None or (len(valid) - 1 - current_start) > (best_end - best_start if best_end is not None else -1):
                best_start, best_end = current_start, len(valid) - 1

        if best_start is None or best_end is None:
            return 0.0

        v_max = v_sweep[best_end]
        v_min = v_sweep[best_start]
        compliance = float(v_max - v_min)
        self.compliance_range_min_max = (v_min, v_max, best_start, best_end)
        if vdd is not None:
            compliance = min(compliance, float(vdd))
        return compliance

    def get_vdd(self):
        """Return the value assigned to a .param entry whose name contains 'vdd'.

        The function scans all .param lines in the provided netlist string and
        returns the first parameter value where the parameter name contains
        the substring 'vdd' (case-insensitive).

        Args:
            netlist: SPICE netlist content as a string.

        Returns:
            The value string assigned to the first matching vdd parameter,
            or None if no matching .param assignment is found.
        """
        netlist = gen_utils.get_file_to_str(self.netlist_path)
        if not isinstance(netlist, str):
            return None
        
        for line in netlist.splitlines():
                # 1. Clean line and convert to lowercase for easy matching
                clean_line = re.split(r"[;*!]", line.strip(), maxsplit=1)[0].strip()
                line_lower = clean_line.lower()

                # 2. Skip empty lines or lines without 'vdd'
                if not clean_line or "vdd" not in line_lower:
                    continue

                # 3. Check if it's a .param line (e.g., ".param vdd=1.2")
                if line_lower.startswith(".param"):
                    match = re.search(r"\bvdd_val\s*=\s*([^\s]+)", line_lower)
                    match2 = re.search(r"\bvdd\s*=\s*([^\s]+)", line_lower)
                    if match:
                        try:
                            return float(match.group(1).strip("{}"))
                        except ValueError:
                            continue  # Found VDD, but it's a variable name, not a number
                    if match2:
                        try:
                            return float(match2.group(1).strip("{}"))
                        except ValueError:
                            continue  # Found VDD, but it's a variable name, not a number

                # 4. Check if it's a Voltage Source line (e.g., "Vvdd vdd 0 dc=1.2")
                elif line_lower.startswith("vdd") and "dc" in line_lower:
                    match = re.search(r"\bdc\s*=?\s*([^\s]+)", line_lower)
                    if match:
                        try:
                            return float(match.group(1).strip("{}"))
                        except ValueError:
                            continue  # Found the DC value, but it's a variable name

        return None

    def _get_best_crossing(cls, xvec, yvec, val):
        interp_fun = interp.InterpolatedUnivariateSpline(xvec, yvec)

        def fzero(x):
            return interp_fun(x) - val

        xstart, xstop = xvec[0], xvec[-1]
        try:
            return sciopt.brentq(fzero, xstart, xstop), True
        except ValueError:
            return xstop, False
    
    def _complex_from_cols(self, data, real_col, imag_col):
        if real_col < data.shape[1] and imag_col < data.shape[1]:
            return data[:, real_col] + 1j * data[:, imag_col]
        raise ("form is not correct while getting complex data ")


    