import shutil

def split_for_window(text, offset=0):
    width = shutil.get_terminal_size((100, 100))[0] # pass a fallback, 1st arg is width
    width -= width//10 # pad by 1/10th
    buf = text.split(" ")
    out = ""
    line = ""
    for w in buf:
        line += w + " "
        cap = width - offset
        while len(line) > cap:
            out += line[:cap] + "\n" + " "*offset
            line= line[cap:]
    out += line
    return out
