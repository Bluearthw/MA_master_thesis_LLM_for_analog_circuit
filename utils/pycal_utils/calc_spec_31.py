def calc_spec_31(data_paths):
    import numpy as np
    import os
    if not data_paths or len(data_paths) < 1:
        return -31.0
    if not os.path.exists(data_paths[0]):
        return -31.1
    try:
        data = np.genfromtxt(data_paths[0], delimiter=',', autostrip=True)
        if len(data.shape) < 2 or data.shape[1] < 2:
            data = np.genfromtxt(data_paths[0], autostrip=True)
        if np.isnan(data[0, 0]):
            data = data[1:]
        t = data[:, 0]
        v = data[:, 1]
        n = len(t)
        if n < 10:
            return -31.2
        start_idx = n // 2
        t_ss = t[start_idx:]
        v_ss = v[start_idx:]
        v_ac = v_ss - np.mean(v_ss)
        zero_crossings = np.where(np.diff(np.sign(v_ac)) != 0)[0]
        if len(zero_crossings) < 2:
            return -31.2
        t_crossings = t_ss[zero_crossings]
        total_time = t_crossings[-1] - t_crossings[0]
        if total_time <= 0:
            return -31.2
        freq = (len(zero_crossings) - 1) / (2.0 * total_time)
        return float(freq)
    except Exception:
        return -31.2