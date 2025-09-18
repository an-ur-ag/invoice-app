from setuptools import setup
import sys

APP = ['silaigo_multiple_page.py']  # Your main Python file
DATA_FILES = ['silaigo_invoice_final.pdf', 'segoeui.ttf']  # Extra files to include
OPTIONS = {
    'argv_emulation': True,
    'includes': ['reportlab', 'PyPDF2', 'tkinter'],  # Include Tkinter explicitly
    'packages': ['tkinter'],
    'iconfile': None,
    'plist': {
        'CFBundleName': 'Invoice Generator',
        'CFBundleShortVersionString': '1.0',
        'CFBundleVersion': '1.0',
        'CFBundleIdentifier': 'com.yourname.invoicegenerator'
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)