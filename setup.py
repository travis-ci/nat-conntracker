import codecs
import os
import sys

from setuptools import setup

_HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(_HERE, *parts), 'r') as fp:
        return fp.read()


def main():
    setup(
        name='nat-conntracker',
        description='Conntrack XML eating NAT thing',
        long_description=read('README.rst'),
        author='Travis CI GmbH',
        author_email='contact+nat-conntracker@travis-ci.org',
        license='MIT',
        url='https://github.com/travis-ci/nat-conntracker',
        use_scm_version=True,
        packages=['nat_conntracker'],
        setup_requires=['pytest-runner>=4.0', 'setuptools_scm>=1.15'],
        install_requires=['cachetools>=2.0', 'redis>=2.10'],
        tests_require=[
            'codecov>=2.0', 'pytest-cov>=2.0', 'pytest-runner>=4.0',
            'pytest>=3.4', 'yapf>=0.22'
        ],
        entry_points={
            'console_scripts':
            ['nat-conntracker=nat_conntracker.__main__:main']
        },
        platforms=['any'],
        zip_safe=False,
        python_requires='>=3.5')
    return 0


if __name__ == '__main__':
    sys.exit(main())
