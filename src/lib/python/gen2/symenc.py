#! /usr/bin/env python
#
# symenc.py -- module for symmetric enscryption using python crypto module
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Fri Jan  7 12:17:04 HST 2011
#]
#
import sys, os.path
from Crypto.Cipher import AES
import crypt
import binascii

# Safer to pass in your own padstr, but this one is provided in case
# you don't
default_padstr = '$%(9H*&_h#w@{}:JR%$#@!~|\//?><,.'

class SymmetricEncryptionObject(object):
    """Convenience object for doing common symmetric encryption/decryption
    operations.  Parameters:
      - secret: symmetric encryption key, will by padded from padstr as
                 necessary
      - padstr: (optional) pass in a padding string to be used for padding
                 the key if needed, defaults to module version
      - salt: a salting string used for making crypt hashes, defaults to
                 the padding string if omitted
      - iv: an initial value used in block chaining ciphers.  If present
                 the stronger AES CBC cipher is used.
    """
    def __init__(self, secret, padstr=None, salt=None, iv=None):
        if not padstr:
            padstr = default_padstr
        self._padstr = padstr
        if not salt:
            salt = self._padstr
        self._salt = salt
        secret = self._padsecret(secret)

        if iv:
            self.ciphermode = 'CBC'
            self.padlen = 16
            iv = iv[:self.padlen]
            iv = iv + self._padstr[:self.padlen-len(iv)]
            assert(len(iv) == self.padlen)
            self._encobj = AES.new(secret, AES.MODE_CBC, iv)
        else:
            self.ciphermode = 'CFB'
            self._encobj = AES.new(secret, AES.MODE_CFB)
            self.padlen = 0

    def _padsecret(self, secret):
        """Used to pad the encryption key out to an appropriate length
        in needed."""
        length = len(secret)
        if length not in (16, 24, 32):
            diff = 32 - length
            return secret + self._salt[:diff]
        else:
            return secret

    def padtext(self, plaintext):
        """Used to pad text to multiples of self.padlen if in CBC mode
        (see http://www.di-mgt.com.au/cryptopad.html)
        """
        if self.ciphermode in ('CBC',):
            # pad 
            length = len(plaintext)
            padlen = self.padlen - (length % self.padlen)
            # could use self._padstr
            padtext = ('\000' * (padlen-1)) + chr(padlen)
            plaintext = plaintext + padtext
        return plaintext
        
    def unpadtext(self, plaintext):
        """Used to unpack text after decryption if necessary.
        (see padtext())
        """
        if self.ciphermode in ('CBC',):
            padlen = ord(plaintext[-1])
            plaintext = plaintext[:-padlen]
        return plaintext
        
    def encrypt(self, plaintext, asciiOnly=True):
        """Encrypt _plaintext_, and convert to ascii unless _asciiOnly_
        is set to False.  Returns ciphertext.
        """
        if self.padlen > 0:
            plaintext = self.padtext(plaintext)
        ciphertext = self._encobj.encrypt(plaintext)
        if asciiOnly:
            return binascii.b2a_hex(ciphertext)
        return ciphertext

    def encrypt_in(self, in_f, asciiOnly=True):
        plaintext = in_f.read()
        return self.encrypt(plaintext, asciiOnly=asciiOnly)
        
    def encrypt_in_out(self, in_f, out_f, asciiOnly=True):
        plaintext = in_f.read()
        ciphertext = self.encrypt(plaintext, asciiOnly=asciiOnly)
        out_f.write(ciphertext)
        
    def encrypt_file(self, infile, outasciiOnly=True):
        with open(infile, 'r') as in_f:
            return self.encrypt_in(in_f, asciiOnly=asciiOnly)
        
    def encrypt_file2file(self, infile, outfile, outasciiOnly=True):
        with open(infile, 'r') as in_f:
            with open(outfile, 'r') as out_f:
                return self.encrypt_in_out(in_f, out_f, asciiOnly=asciiOnly)
        
    def decrypt(self, ciphertext, asciiOnly=True):
        """Decrypt _ciphertext_ and return plaintext.  _ciphertext_ is
        assumed to be ascii-encoded unless _asciiOnly_ is set to False.
        """
        if asciiOnly:
            ciphertext = binascii.a2b_hex(ciphertext)
        plaintext = self._encobj.decrypt(ciphertext)
        if self.padlen > 0:
            plaintext = self.unpadtext(plaintext)
        return plaintext

    def decrypt_in(self, in_f, asciiOnly=True):
        ciphertext = in_f.read()
        return self.decrypt(ciphertext, asciiOnly=asciiOnly)
        
    def decrypt_in_out(self, in_f, out_f, asciiOnly=True):
        ciphertext = in_f.read()
        plaintext = self.decrypt(ciphertext, asciiOnly=asciiOnly)
        out_f.write(plaintext)
        
    def decrypt_file(self, infile, outasciiOnly=True):
        with open(infile, 'r') as in_f:
            return self.decrypt_in(in_f, asciiOnly=asciiOnly)
        
    def decrypt_file2file(self, infile, outfile, outasciiOnly=True):
        with open(infile, 'r') as in_f:
            with open(outfile, 'r') as out_f:
                return self.decrypt_in_out(in_f, out_f, asciiOnly=asciiOnly)
        
    def mkhash(self, plaintext):
        """Make a crypt compatible hash for use in storing password
        files, etc.  Takes _plaintext_ and returns a crypt hash.
        """
        return crypt.crypt(plaintext, self._salt)
    

def main(options, args):

    if options.keyfile:
        with open(options.keyfile, 'r') as key_f:
            key = key_f.read().strip()
    else:
        key = options.key
            
    if options.ivfile:
        with open(options.ivfile, 'r') as iv_f:
            iv = iv_f.read().strip()
    elif options.iv:
        iv = options.iv
    else:
        iv = None
            
    if options.padfile:
        with open(options.padfile, 'r') as pad_f:
            padstr = pad_f.read()
    elif options.padstr:
        padstr = options.padstr
    else:
        padstr = None
            
    if options.saltfile:
        with open(options.saltfile, 'r') as salt_f:
            salt = salt_f.read()
    elif options.salt:
        salt = options.salt
    else:
        salt = None
            
    obj = SymmetricEncryptionObject(key, padstr=padstr, salt=salt, iv=iv)

    if options.outfile and os.path.exists(options.outfile):
        print "File exists: %s" % options.outfile
        sys.exit(1)
        
    if options.infile:
        in_f = open(options.infile, 'r')
    else:
        inbuf = sys.stdin
        
    if options.outfile:
        out_f = open(options.outfile, 'w')
    else:
        out_f = sys.stdout
        
    if options.action == 'encrypt':
        obj.encrypt_in_out(in_f, out_f, asciiOnly=options.asciionly)
    elif options.action == 'decrypt':
        obj.decrypt_in_out(in_f, out_f, asciiOnly=options.asciionly)
    else:
        print "I don't understand action '%s'!" % (options.action)

    out_f.close()
    in_f.close()

if __name__ == '__main__':
    # Parse command line options
    from optparse import OptionParser

    usage = "usage: %prog [options]"
    optprs = OptionParser(usage=usage, version=('%%prog'))
    
    optprs.add_option("-b", "--binary", dest="asciionly", default=True,
                      action="store_false",
                      help="Do not convert the result to ASCII")
    optprs.add_option("--debug", dest="debug", default=False, action="store_true",
                      help="Enter the pdb debugger on main()")
    optprs.add_option("-a", "--action", dest="action",
                      help="Action to perform (encrypt|decrypt")
    optprs.add_option("-i", "--in", dest="infile", metavar='FILE',
                      help="Read input from FILE")
    optprs.add_option("--iv", dest="iv", default=None,
                      help="Specify initial IV for AES CBC decoding")
    optprs.add_option("--ivfile", dest="ivfile", default=None,
                      metavar='FILE',
                      help="Specify FILE containing initial IV for AES CBC decoding")
    optprs.add_option("--profile", dest="profile", action="store_true",
                      default=False,
                      help="Run the profiler on main()")
    optprs.add_option("-o", "--out", dest="outfile", metavar='FILE',
                      help="Write output to FILE")
    optprs.add_option("-k", "--key", dest="key", default=None,
                      metavar='KEY',
                      help="Specify symmetric encryption key")
    optprs.add_option("-f", "--keyfile", dest="keyfile", default=None,
                      metavar='FILE',
                      help="Specify FILE containing symmetric encryption key")
    optprs.add_option("-p", "--pad", dest="padstr", default=None,
                      help="Specify padding for padding key")
    optprs.add_option("--padfile", dest="padfile", default=None,
                      metavar='FILE',
                      help="Specify FILE containing padding")
    optprs.add_option("-s", "--salt", dest="salt", default=None,
                      help="Specify salt for padding key")
    optprs.add_option("--saltfile", dest="saltfile", default=None,
                      metavar='FILE',
                      help="Specify FILE containing salt")

    (options, args) = optprs.parse_args(sys.argv[1:])

    if len(args) != 0:
        optprs.error("incorrect number of arguments")

    if (not options.key) and (not options.keyfile):
        optprs.error("Please specify a --key or --keyfile")
    if not options.action:
        optprs.error("Please specify an --action")

    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print "%s profile:" % sys.argv[0]
        profile.run('main(options, args)')

    else:
        main(options, args)
       
    
#END
