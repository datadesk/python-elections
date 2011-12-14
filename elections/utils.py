def split_len(seq, length):
    return [seq[i:i+length] for i in range(0, len(seq), length)]

def strip_dict(d):
    """
    Strip all leading and trailing whitespace in dictionary keys and values.
    """
    return dict((k.strip(), v.strip()) for k, v in d.items())
    

