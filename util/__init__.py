def batchify(str_in, size):
    if len(str_in) < size:
        return [str_in]
    out = []
    for i in range((len(str_in)//size) + 1):
        out.append(str_in[i*size : (i+1)*size])
    return out

