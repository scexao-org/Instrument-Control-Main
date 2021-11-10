def isfloat (instr):
    chkstr = str(instr)
    
    if chkstr[:1] == "-" or chkstr[:1] == "+":
        chkstr = chkstr[1:]
    numsplit = chkstr.split('.')
    if len(numsplit) == 1:
        if numsplit[0].isdigit():
            return True
        else:
            return False
    elif len(numsplit) == 2:
        if numsplit[0] == '':
            numsplit[0] = '0'
        if numsplit[0].isdigit() and numsplit[1].isdigit():
            return True
        else:
            return False
    else:
        return False


