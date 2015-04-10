from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pisc',
      version='0.1',
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