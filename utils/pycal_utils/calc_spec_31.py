def calc_spec_31(data_paths):
    import numpy as np
    import os
    if not data_paths or len(data_paths) < 1:
        return -31.0
    if not os.path.exists(data_paths[0]):
        return -31.1
    try:
        data = np.genfromtxt(data_paths[0], autostrip=True, skip_header=1)
        if data.ndim != 2 or data.shape[1] < 2:
            data = np.genfromtxt(data_paths[0], autostrip=True)
        t = data[:, 0]
        v = data[:, 1]
        n = len(t)
        t = t[n//2:]
        v = v[n//2:]
        v_ac = v - np.mean(v)
        zero_crossings = np.where((v_ac[:-1] <= 0) & (v_ac[1:] > 0))[0]
        if len(zero_crossings) < 2:
            return -31.2
        t_cross = []
        for idx in zero_crossings:
            t1, t2 = t[idx], t[idx+1]
            v1, v2 = v_ac[idx], v_ac[idx+1]
            t_c = t1 - v1 * (t2 - t1) / (v2 - v1)
            t_cross.append(t_c)
        periods = np.diff(t_cross)
        freq = 1.0 / np.mean(periods)
        return float(freq)
    except Exception:
        return -31.2