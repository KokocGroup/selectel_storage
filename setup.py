from setuptools import setup


VERSION = "0.0.4"

setup(
    name='selectel-storage',
    description="",
    version=VERSION,
    url='https://github.com/KokocGroup/selectel_storage',
    download_url='https://github.com/KokocGroup/selectel_storage/tarball/v{}'.format(VERSION),
    packages=['selectel_storage'],
    package_dir={'selectel_storage': 'selectel_storage'},
    install_requires=[
        'mongoengine==0.10.0',
        'selectel-api==0.1.3',
        'python-magic==0.4.10'
    ],
)
