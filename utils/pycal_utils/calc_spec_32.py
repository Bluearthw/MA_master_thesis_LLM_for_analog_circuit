def calc_spec_32(raw_data):
    import numpy as np
    if raw_data is None:
        return -32.0
    try:
        vctrl = np.round(raw_data[:, 1], 3)
        unique_ctrls = np.unique(vctrl)
        freqs = []
        ctrl_vals = []
        for ctrl in unique_ctrls:
            mask = (vctrl == ctrl)
            t_sub = raw_data[mask, 0]
            v_sub = raw_data[mask, 2]
            if len(t_sub) < 10:
                continue
            v_detrend = v_sub - np.mean(v_sub)
            zero_crossings = np.where(np.diff(np.sign(v_detrend)))[0]
            if len(zero_crossings) >= 3:
                t_cross = t_sub[zero_crossings]
                period = 2.0 * np.mean(np.diff(t_cross))
                if period > 0:
                    freqs.append(1.0 / period)
                    ctrl_vals.append(ctrl)
        if len(freqs) >= 2 and (max(ctrl_vals) - min(ctrl_vals)) > 0:
            kvco = (max(freqs) - min(freqs)) / (max(ctrl_vals) - min(ctrl_vals))
            return float(kvco)
        print("Insufficient data for spec_id: 32")
        return 0.0
    except Exception:
        print("Error occurred while calculating spec_id: 32")
        return 0.0