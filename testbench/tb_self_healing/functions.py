def measurement(id):
    if id == 1:
        return get_dc_gain()
    elif id == 2:
        return get_psrr()
    elif id == 3:
        return get_requirement_3()

    elif id == 4:
        return get_requirement_4()
    # [INSERT_NEW_BRANCH_HERE]
    
def get_dc_gain():
    return 0

def get_psrr():
    return 10

def get_requirement_3():
    return 3 * 10  # Automatically healed


def get_requirement_4():
    return 4 * 10  # Automatically healed
