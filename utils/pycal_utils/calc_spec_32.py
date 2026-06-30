def calc_spec_32(raw_data):
    import numpy as np
    if raw_data is None:
        return -32.0
    try:
        if not isinstance(raw_data, np.ndarray) or raw_data.ndim != 2:
            return -32.1
        def estimate_freq(t, v):
            n = len(t)
            if n < 10:
                return None
            start_idx = n // 2
            t_s = t[start_idx:]
            v_s = v[start_idx:]
            v_centered = v_s - np.mean(v_s)
            zero_crossings = np.where(np.diff(np.sign(v_centered)) != 0)[0]
            if len(zero_crossings) < 3:
                return None
            t_cross = []
            for idx in zero_crossings:
                t1, t2 = t_s[idx], t_s[idx+1]
                v1, v2 = v_centered[idx], v_centered[idx+1]
                if v2 - v1 != 0:
                    t_cross.append(t1 - v1 * (t2 - t1) / (v2 - v1))
            t_cross = np.array(t_cross)
            diffs = np.diff(t_cross)
            mean_half_period = np.mean(diffs)
            if mean_half_period <= 0:
                return None
            return 1.0 / (2.0 * mean_half_period)
        cols = raw_data.shape[1]
        if cols >= 6:
            f_low = estimate_freq(raw_data[:, 0], raw_data[:, 1])
            f_high = estimate_freq(raw_data[:, 4], raw_data[:, 5])
        elif cols >= 4:
            f_low = estimate_freq(raw_data[:, 0], raw_data[:, 1])
            f_high = estimate_freq(raw_data[:, 0], raw_data[:, 3])
        elif cols >= 2:
            f_low = estimate_freq(raw_data[:, 0], raw_data[:, 1])
            f_high = f_low
        else:
            return -32.2
        if f_low is None or f_high is None:
            return -32.3
        tuning_range = f_high - f_low
        return float(tuning_range)
    except Exception:
        return -32.4