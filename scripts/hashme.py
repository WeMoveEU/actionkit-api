import os
import sys
import base64
import hashlib

to_hash = sys.argv[1]

sha = hashlib.sha256("{0}.{1}".format(os.getenv("ACTIONKIT_SECRET_KEY"), to_hash).encode("ascii"))
raw_hash = sha.digest()
urlsafe_hash = base64.urlsafe_b64encode(raw_hash).decode("ascii")

print(to_hash + '.' + urlsafe_hash[:6])
