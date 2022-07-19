import pyDes
import base64

#Key = "PASSWORD"
Key="16df7fa2641fa89d"
Iv = None

def bytesToHexString(bs):
	return ''.join(['%02X ' % b for b in bs])

def hexStringTobytes(str):
	str = str.replace(" ", "")
	return bytes.fromhex(str)

def encrypt_str(data):
	secret_key=hexStringTobytes(Key)
	method = pyDes.des(secret_key, pyDes.ECB, Iv, pad=None, padmode=pyDes.PAD_PKCS5)
	k = method.encrypt(data)
	data = bytesToHexString(k).replace(' ','')
	return data.lower()

def decrypt_str(data):
	secret_key=hexStringTobytes(Key)
	method = pyDes.des(secret_key, pyDes.ECB, Iv, pad=None, padmode=pyDes.PAD_PKCS5)
	k =hexStringTobytes(data)
	return method.decrypt(k)

Encrypt = encrypt_str("Hello World Bye Bye yeah")
print(Encrypt)
Decrypt = decrypt_str(Encrypt)
print(Decrypt)

# Hello World Bye Bye yeah -> 668bd2d639a4f59aa26fefb5fec763203140995770df0d52883bd203ed9e297b
