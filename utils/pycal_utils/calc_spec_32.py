def calc_spec_32(data_paths):
    import numpy as np
    import os
    if not data_paths or len(data_paths) < 3:
        return -32.0
    for p in data_paths[:3]:
        if not os.path.exists(p):
            return -32.1
    try:
        freqs = []
        for path in data_paths[:3]:
            data = np.genfromtxt(path, delimiter=',', autostrip=True)
            if len(data.shape) < 2 or data.shape[1] < 2:
                data = np.genfromtxt(path, autostrip=True)
            if np.isnan(data[0, 0]):
                data = data[1:]
            t = data[:, 0]
            v = data[:, 1]
            n = len(t)
            if n < 10:
                return -32.2
            start_idx = n // 2
            t_ss = t[start_idx:]
            v_ss = v[start_idx:]
            v_ac = v_ss - np.mean(v_ss)
            zero_crossings = np.where(np.diff(np.sign(v_ac)) != 0)[0]
            if len(zero_crossings) < 2:
                return -32.2
            t_crossings = t_ss[zero_crossings]
            total_time = t_crossings[-1] - t_crossings[0]
            if total_time <= 0:
                return -32.2
            freq = (len(zero_crossings) - 1) / (2.0 * total_time)
            freqs.append(freq)
        tuning_range = freqs[2] - freqs[0]
        return float(tuning_range)
    except Exception:
        return -32.2