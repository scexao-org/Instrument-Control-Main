from distutils.core import setup, Extension
import os

sossinc = os.path.join(os.environ['SOSSHOME'], 'include')
sosslib = os.path.join(os.environ['SOSSHOME'], 'lib')

module1 = Extension('rtd',
                    define_macros = [('MAJOR_VERSION', '1'),
                                     ('MINOR_VERSION', '0')],
                    include_dirs = [sossinc],
                    libraries = ['rtdImgEvt', 'rtdRemote'],
                    library_dirs = [sosslib],
                    sources = ['rtd.c'])

setup (name = 'rtd',
       version = '1.0',
       description = 'Client interface to the Real Time Data server',
       author = 'Eric Jeschke',
       author_email = 'eric@naoj.org',
       url = 'http://subarutelescope.org/staff/eric',
       long_description = '''
This is really just a demo package.
''',
       ext_modules = [module1])

