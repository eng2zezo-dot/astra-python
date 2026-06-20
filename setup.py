from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='astra-python',
    version='0.1.0',
    author='Astra Python Contributors',
    description='A professional Headend Software system for TV distribution',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/eng2zezo-dot/astra-python',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Topic :: Multimedia :: Video',
        'Topic :: System :: Networking',
    ],
    python_requires='>=3.9',
    entry_points={
        'console_scripts': [
            'astra=astra.main:cli',
        ],
    },
)
