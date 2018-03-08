import codecs
import os
import subprocess
import sys

from setuptools import setup, find_packages

_HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(_HERE, *parts), 'r') as fp:
        return fp.read()


def get_version():
    return subprocess.check_output(
        ['git', 'describe', '--always', '--dirty', '--tags']
    ).decode('utf-8').strip()


def write_version_file(version):
    version_file = os.path.join(_HERE, 'nat_conntracker', '__version__.py')
    with open(version_file, 'w') as fp:
        fp.write('# WARNING: this is a generated file\n\n')
        fp.write('VERSION = {!r}\n'.format(version))


def main():
    version = get_version()
    write_version_file(version)

    setup(
        name='nat-conntracker',
        version=version,
        description='Conntrack XML eating NAT thing',
        long_description=read('README.rst'),
        author='Travis CI GmbH',
        author_email='contact+nat-conntracker@travis-ci.org',
        license='MIT',
        url='https://github.com/travis-ci/nat-conntracker',
        packages=find_packages(exclude=['tests']),
        setup_requires=[
            'pytest-runner>=4.0'
        ],
        install_requires=[
            'netaddr>=0.7',
            'redis>=2.10'
        ],
        tests_require=[
            'codecov>=2.0',
            'flake8>=3.5',
            'pytest>=3.4',
            'pytest-cov>=2.0',
            'pytest-runner>=4.0'
        ],
        entry_points={
            'console_scripts': [
                'nat-conntracker=nat_conntracker.__main__:main'
            ]
        },
        platforms=['any'],
        zip_safe=False,
        python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*'
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
