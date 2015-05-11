from setuptools import setup
from pisc.sensor_startup import current_pisc_version

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pisc',
      version=current_pisc_version,
      description='Platform Independent Sensor Control',
      long_description=readme(),
      keywords='sensor htp phenotyping',
      url='TODO',
      author='',
      author_email='',
      license='TODO',
      packages=['pisc'],
      install_requires=[
          'pyserial',
      ],
      zip_safe=False)