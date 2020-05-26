from flask import escape

def str_sanitize(string):
    return escape(string.strip())

def van_obfuscate(val): 
    print(val)
    if val == None: 
        return None

    if isinstance(val, str) and not val.isdigit():
        return ''

    t = int(val)
    i = t % 17
    r = chr(65 + i)
    u = hex(t).replace('0x', '').upper()
    f = ''.join(reversed(u))

    print('EID' + f + r)
    return 'EID' + f + r