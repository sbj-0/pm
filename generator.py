import secrets, string

def generate_password(length=16, use_symbols=True, avoid_ambiguous=True):
    if length < 8:
        raise ValueError("Passwords must have at least 8 characters.")
    alpha = (
    string.ascii_letters +
    string.digits + string.punctuation
    )
    if use_symbols is False:
        alpha = alpha.translate(str.maketrans("", "", string.punctuation))
    if avoid_ambiguous:
        alpha = alpha.translate(str.maketrans('', '', '0Oo1l|I'))
    while True:
        pswd = ''.join(secrets.choice(alpha) for _ in range(length))
        
        if (any(c.islower() for c in pswd) and
            any(c.isupper() for c in pswd) and
            any(c.isdigit() for c in pswd)):
            return pswd
    

generate_password()