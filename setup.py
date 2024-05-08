from setuptools import setup, find_packages

setup(
    name='3d-nand-optimization-tool',
    version='1.0.0',
    description='A tool for optimizing 3D NAND flash storage systems',
    author='Mudit Bhargava',
    author_email='muditbhargava666@gmail.com.com',
    url='https://github.com/muditbhargava66/3D-NAND-Flash-Storage-Optimization-Tool.git',
    packages=find_packages(),
    python_requires='>=3.7, <3.11',
    install_requires=[
        'numpy>=1.23.5',
        'pandas>=1.5.3',
        'PyYAML>=6.0',
        'matplotlib>=3.7.1',
        'seaborn>=0.12.2',
        'scipy>=1.10.1',
        'bchlib>=1.0.1',
        'pyldpc>=0.7.9',
        'lz4>=4.3.2',
        'zstd>=1.5.4.0',
        'PyQt5>=5.15.9'
    ],
    entry_points={
        'console_scripts': [
            '3d-nand-optimization-tool=src.main:main'
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)