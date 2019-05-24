

import sys
import py2exe
import shutil
from distutils.core import setup


sys.argv.append('py2exe')
setup(
    windows=[{"script":"point_cloud_transformer.py"}],
    options={"py2exe":{"includes":["sip", "PyQt4.QtXml"]}}
)
