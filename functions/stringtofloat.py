# Parse a given string into a float. Mainly we handle the special cases
# of when a special character is unexpectedly used in place of the minus
# sign.
# https://jkorpela.fi/dashes.html
def string_to_float(string):
    string = string.replace("-","-")
    string = string.replace("־","-")
    string = string.replace("‐","-")
    string = string.replace("‑","-")
    string = string.replace("‒","-")
    string = string.replace("–","-")
    
    string = string.replace("—","-")
    string = string.replace("―","-")
    string = string.replace("⁻","-")
    string = string.replace("₋","-")
    string = string.replace("−","-")
    string = string.replace("﹘","-")
    string = string.replace("﹣","-")
    string = string.replace("－","-")
    return float(string)
