from setuptools import find_namespace_packages
from setuptools import setup

version = '0.1.0.dev0'

setup(
    name='e2e.api',
    version=version,
    description="REST API wrappers & modeling framework for APIs.",
    url='https://github.com/nickroeker/e2e.api',
    author="Nic Kroeker",
    author_email='',
    license='Apache 2.0',
    packages=find_namespace_packages(include=['e2e.*']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Testing :: Acceptance',
    ],
    install_requires=[
        'requests>=2.1.0',
        'typing;python_version<"3.5"',
    ],
    extras_require={
        'dev': [
            'tox',
            'pytest'
            'requests_mock',
            'responses',
            'setuptools>="40.1.0"',
        ]
    },
)
