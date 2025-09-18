from setuptools import setup

APP = ['silaigo_multiple_page.py']
DATA_FILES = ['silaigo_invoice_final.pdf', 'segoeui.ttf']
OPTIONS = {
    'argv_emulation': True,
    'includes': ['reportlab', 'PyPDF2'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)