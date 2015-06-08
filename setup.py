from setuptools import setup

current_pisc_version = '0.0'
current_config_version = '0.0'

def readme():
    with open('README.rst') as f:
        return f.read()

if __name__ == "__main__":
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