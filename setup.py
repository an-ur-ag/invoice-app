from setuptools import setup

APP = ['your_main_file.py']  # Replace with your main .py filename
DATA_FILES = ['silaigo_invoice_final.pdf', 'segoeui.ttf']  # Any extra files your app needs
OPTIONS = {
    'argv_emulation': True,
    'includes': ['reportlab', 'PyPDF2'],
    'iconfile': None,
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)