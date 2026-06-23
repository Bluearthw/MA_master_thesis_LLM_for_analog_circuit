def calc_spec_31(raw_data):
    import numpy as np
    if raw_data is None:
        return -31.0
    try:
        t = raw_data[:, 0]
        v = raw_data[:, 1]
        v_detrend = v - np.mean(v)
        zero_crossings = np.where(np.diff(np.sign(v_detrend)))[0]
        if len(zero_crossings) < 3:
            return 0.0
        t_cross = t[zero_crossings]
        period = 2.0 * np.mean(np.diff(t_cross))
        if period <= 0:
            return 0.0
        return float(1.0 / period)
    except Exception:
        return 0.0