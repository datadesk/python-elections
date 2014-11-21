from setuptools import setup


setup(
    name='python-elections',
    version='1.1.3',
    description="A Python wrapper for the AP's U.S. election data service.",
    author='The Los Angeles Times Data Desk',
    author_email='datadesk@latimes.com',
    url='http://www.github.com/datadesk/python-elections/',
    packages=("elections",),
    install_requires=[
        'latimes-calculate==0.1.8',
        'python-dateutil==1.5',
        'BeautifulSoup==3.2.1',
    ],
    classifiers=(
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    )
)
