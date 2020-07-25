from setuptools import setup, find_packages, Extension
from pathlib import Path

here = Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

class quicklz:

  path = here / 'src' / 'quicklz'

  defines = dict(
    QLZ_COMPRESSION_LEVEL=3,
    QLZ_STREAMING_BUFFER=0,
    QLZ_MEMORY_SAFE=1)

  extension = Extension('bimxplode.quicklz',
    define_macros=list(defines.items()),
    include_dirs=[path],
    sources=[str(p) for p in path.glob('**/*.c')])

setup(

  name='bimxplode',
  version='0.1.1',
  description='A tool for extracting ARCHICAD BIMx hyper-models',

  long_description=long_description,
  long_description_content_type='text/markdown',

  author='James Kirkwood',

  url='https://github.com/jameskirkwood/bimxplode',
  project_urls={
    'Bug Reports': 'https://github.com/jameskirkwood/bimxplode/issues',
    'Source': 'https://github.com/jameskirkwood/bimxplode',
  },

  classifiers=[
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Operating System :: POSIX',
    'Programming Language :: Python :: 3 :: Only',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3',
    'Topic :: Multimedia :: Graphics :: Graphics Conversion',
    'Topic :: System :: Archiving',
  ],

  package_dir={'': 'src'},
  packages=find_packages(where='src'),
  ext_modules=[quicklz.extension],

  python_requires='>=3.5, <4',
  install_requires=[
    'numpy',
    'pygltflib',
  ],

  entry_points={
    'console_scripts': [
      'bxpk=bimxplode.main:bxpk_main',
      'zres=bimxplode.main:zres_main',
    ],
  },
)
