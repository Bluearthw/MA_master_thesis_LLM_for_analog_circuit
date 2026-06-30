def calc_spec_31(raw_data):
    import numpy as np
    if raw_data is None:
        return -31.0
    try:
        if not isinstance(raw_data, np.ndarray) or raw_data.ndim != 2 or raw_data.shape[1] < 2:
            return -31.1
        t = raw_data[:, 0]
        v = raw_data[:, 1]
        n = len(t)
        if n < 10:
            return -31.2
        start_idx = n // 2
        t_s = t[start_idx:]
        v_s = v[start_idx:]
        v_centered = v_s - np.mean(v_s)
        zero_crossings = np.where(np.diff(np.sign(v_centered)) != 0)[0]
        if len(zero_crossings) < 3:
            return -31.3
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
            return -31.4
        freq = 1.0 / (2.0 * mean_half_period)
        return float(freq)
    except Exception:
        return -31.5