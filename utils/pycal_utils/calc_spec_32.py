def calc_spec_32(data_paths):
    import numpy as np
    import os
    if not data_paths or len(data_paths) < 3:
        return -32.0
    for p in data_paths[:3]:
        if not os.path.exists(p):
            return -32.1
    try:
        def get_freq(path):
            data = np.genfromtxt(path, autostrip=True, skip_header=1)
            if data.ndim != 2 or data.shape[1] < 2:
                data = np.genfromtxt(path, autostrip=True)
            t = data[:, 0]
            v = data[:, 1]
            n = len(t)
            t = t[n//2:]
            v = v[n//2:]
            v_ac = v - np.mean(v)
            zero_crossings = np.where((v_ac[:-1] <= 0) & (v_ac[1:] > 0))[0]
            if len(zero_crossings) < 2:
                raise ValueError("Not enough crossings")
            t_cross = []
            for idx in zero_crossings:
                t1, t2 = t[idx], t[idx+1]
                v1, v2 = v_ac[idx], v_ac[idx+1]
                t_c = t1 - v1 * (t2 - t1) / (v2 - v1)
                t_cross.append(t_c)
            periods = np.diff(t_cross)
            return 1.0 / np.mean(periods)
        freq_low = get_freq(data_paths[0])
        freq_high = get_freq(data_paths[2])
        tuning_range = freq_high - freq_low
        gain = tuning_range / 1.0
        return float(gain)
    except Exception:
        return -32.2