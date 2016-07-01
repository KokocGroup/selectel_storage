from setuptools import setup, find_packages


VERSION = "0.0.23"

setup(
    name='selectel-storage',
    description="",
    version=VERSION,
    url='https://github.com/KokocGroup/selectel_storage',
    download_url='https://github.com/KokocGroup/selectel_storage/tarball/v{}'.format(VERSION),
    packages=find_packages(),
    install_requires=[
        'mongoengine==0.10.0',
        'python-magic==0.4.10',
        'requests==2.10.0'
    ],
)
