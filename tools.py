def get_percentage(value, total, multiply=True):
    if not isinstance(value, (int,long,float)):
        return ValueError('Input values should be a number, your first input is a %s' % type(value))
    if not isinstance(total, (int,long,float)):
        return ValueError('Input values should be a number, your second input is a %s' % type(total))
    try:
        percent = (value / float(total))
        if multiply:
            percent = percent * 100
        return percent
    except ZeroDivisionError:
        return 0.0

def split_len(seq, length):
    return [seq[i:i+length] for i in range(0, len(seq), length)]
