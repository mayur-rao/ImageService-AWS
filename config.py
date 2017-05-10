#from passlib.hash import sha256_crypt
#from Crypto.Cipher import AES
#import hashlib

host="****"    # your host, usually localhost
user="****"        # your username
passwd="****" # your password
db="****"        # name of the data base
secret_key_file = '****'
enc_password = 'samaritan'
#key = hashlib.sha256(enc_password).digest()
#IV = 16 * '\x00'           # Initialization vector: discussed later
#mode = AES.MODE_CBC

temp_path = '****'
ALLOWED_EXTENSION = set([ 'jpeg', 'jpg', 'png', 'PNG', 'gif', 'GIF', 'mp4', 'txt', 'pdf'])

user_reg = '^[a-z0-9_-]{3,15}$'
user_passv = '^[a-z0-9_-]{3,18}$'

access_key = "****"
secret_key = "****"
region_host = "****"
buck_name = "****"
buck_name_other = "****"
auth_file = "auth_users.txt"
auth_file_path = "eb-scalin/static/auth_users.txt"
img_file_path = "eb-scalin/static/images/"

redis_host = "****"

