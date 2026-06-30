def calc_spec_32(raw_data):
    if raw_data is None:
        return -32.0
    import numpy as np
    try:
        if raw_data.ndim != 2:
            return -32.1
        cols = raw_data.shape[1]
        if cols >= 6:
            t_low, v_low = raw_data[:, 0], raw_data[:, 1]
            t_mid, v_mid = raw_data[:, 2], raw_data[:, 3]
            t_high, v_high = raw_data[:, 4], raw_data[:, 5]
        elif cols >= 4:
            t_low = t_mid = t_high = raw_data[:, 0]
            v_low = raw_data[:, 1]
            v_mid = raw_data[:, 2]
            v_high = raw_data[:, 3]
        else:
            return -32.2
        
        def get_freq(t, v):
            mask = ~np.isnan(t) & ~np.isnan(v)
            t = t[mask]
            v = v[mask]
            n = len(t)
            if n < 10:
                return 0.0
            t_steady = t[n // 2:]
            v_steady = v[n // 2:]
            v_ac = v_steady - np.mean(v_steady)
            zero_cross = np.where(np.diff(np.sign(v_ac)))[0]
            if len(zero_cross) < 3:
                return 0.0
            t_cross = t_steady[zero_cross]
            periods = np.diff(t_cross[::2])
            if len(periods) == 0:
                return 0.0
            return 1.0 / np.mean(periods)

        f_low = get_freq(t_low, v_low)
        f_mid = get_freq(t_mid, v_mid)
        f_high = get_freq(t_high, v_high)
        
        if f_low == 0.0 or f_high == 0.0:
            return -32.3
            
        tuning_range = abs(f_high - f_low)
        return float(tuning_range)
    except Exception:
        return -32.4