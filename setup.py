from setuptools import find_packages, setup

package_name = 'grift'

setup(name=package_name,
      version='0.5.1',
      packages=find_packages(),
      package_data={package_name + '.tests': ['*.json']},
      install_requires=[
          'schematics==1.1.1',
          'requests==2.13.0'
      ],
      )
