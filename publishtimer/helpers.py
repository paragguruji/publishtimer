# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 12:51:03 2016

@author: Parag Guruji, paragguruji@gmail.com
"""

import os
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Hash import MD5


CONF_PATH = 'conf/local.env'
BLOCK_SIZE = 16


def setup_env(conf_path=''):
    """Sets up environment variables as specified in the file at CONF_PATH
    """
    if not conf_path:
        conf_path = CONF_PATH
    try:
        environfile = open(conf_path)
    except:
        return False
    for line in environfile:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        key_val = line.split('=')
        if len(key_val) == 2:    
            os.environ[key_val[0].strip()] = key_val[1].strip()
    return True


def decrypt(base64binary_input, raw_key=None):
    """Decrypts the data received from Crowdfire access details API
    """
    if not base64binary_input:
        return None
    if not raw_key:
        raw_key = os.environ.get('ENCRYPTION_KEY', None)
    ciphertext = buffer(bytearray(map(ord, b64decode(base64binary_input))))
    #print "Raw_key:", raw_key
    key = MD5.new(bytearray(raw_key)).digest()
    iv = buffer(bytearray('0'*BLOCK_SIZE))
    cipher = AES.new(key=key, mode=AES.MODE_CBC, IV=iv)        
    unpad = lambda s : s[0:-ord(s[-1])]
    return unpad(cipher.decrypt(ciphertext))


def pad(s):
    """Utility function for padding data with block size = BLOCK_SIZE
    """
    return s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)


def unpad(s):
    """Utility function for unpadding data with block size = BLOCK_SIZE
    """
    return s[:-ord(s[len(s)-1:])]


def purge_key_deep(a_dict, key):
    """Removes given key from all nested levels of a_dict
    """
    try:
        a_dict.pop(key)
    except KeyError:
        pass
    for k in a_dict.keys():
        if isinstance(a_dict[k], dict):
            a_dict[k] = purge_key_deep(a_dict[k], key)
    return a_dict
        

if __name__=="__main__":
    setup_env()