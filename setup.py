import codecs
import os
import sys

from setuptools import setup, find_packages

_HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(_HERE, *parts), 'r') as fp:
        return fp.read()


def main():
    setup(
        name='nat-conntracker',
        version='0.1.0',
        description='Conntrack XML eating NAT thing',
        long_description=read('README.rst'),
        author='Travis CI GmbH',
        author_email='contact+nat-conntracker@travis-ci.org',
        license='MIT',
        url='https://github.com/travis-ci/nat-conntracker',
        packages=find_packages(exclude=['tests']),
        setup_requires=['pytest-runner'],
        install_requires=['netaddr>=0.7'],
        entry_points={
            'console_scripts': [
                'nat-conntracker=nat_conntracker.__main__:main'
            ]
        },
        platforms=['any'],
        tests_require=['pytest'],
        zip_safe=False,
        python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
