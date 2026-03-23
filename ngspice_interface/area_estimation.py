class BPTM45nmAreaEstimator:
    def __init__(self, circuit_params, circuit_multipliers):
        self.circuit_params = circuit_params
        self.circuit_multipliers = circuit_multipliers
    
    def find_area(self):
        area = 0.0

        # build transistor list correctly
        transistors = {}
        for key in self.circuit_params:
            # only pick the multiplier names (mn1, mp1, mn3, ...)
            if key.startswith('m') and key[1].isalpha():
                base = key[1:]   # n1 → 'n1', p3 → 'p3', etc.
                try:
                    m = float(self.circuit_params[key])
                    w = float(self.circuit_params['w' + base])
                    l = float(self.circuit_params['l' + base])
                    transistors[key] = (m, w, l)
                except KeyError as e:
                    print(f"[Warning] missing {e} for transistor {key}")
                    continue

        # accumulate area contributions
        for param_name, mult in self.circuit_multipliers.items():
            if param_name in transistors:          # transistor
                m, w, l = transistors[param_name]
                area += self.compute_transistor_area(m, w, l) * mult

            elif param_name == 'res' and 'res' in self.circuit_params:
                area += self.compute_resistor_area(self.circuit_params['res']) * mult

            elif param_name == 'cap' and 'cap' in self.circuit_params:
                area += self.compute_capacitor_area(self.circuit_params['cap']) * mult

            else:
                print(f"[Warning] skipping unknown device '{param_name}'")

        return area


            
    
    def compute_transistor_area(self, m, w, l):
        Wext = 50e-9 # 50 nm
        Lext = 160e-9 # 160 nm

        one_finger_area = w * l + 2 * (w * Lext + Wext * l)
        all_fingers_area = m * one_finger_area

        return all_fingers_area

    def compute_capacitor_area(self, c):
        # (1e-6)**2 --> um^2  ,  1e-15 --> fF
        farad_to_area_ratio = (100 * (1e-6)**2) / (300 * 1e-15)
        cap_area = c * farad_to_area_ratio

        return cap_area

    def compute_resistor_area(self, r):
        ohm_to_area_ratio = (1e-6)**2 / 14
        res_area = r * ohm_to_area_ratio

        return res_area