from pwdlib import PasswordHasher

ph = PasswordHasher.recommended()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15