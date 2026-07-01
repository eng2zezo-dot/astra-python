#!/usr/bin/env python3
"""Setup script for Astra Headend."""

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

with open('requirements.txt', 'r', encoding='utf-8') as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith('#')]

setup(
    name='astra-headend',
    version='1.0.0',
    author='Eng2zezo',
    author_email='eng2zezo@gmail.com',
    description='MPEG-2 TS Headend System - Professional broadcast playout and stream processing',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/eng2zezo-dot/astra-python',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Telecommunications Industry',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Video',
    ],
    python_requires='>=3.8',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'astra=astra.main:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
