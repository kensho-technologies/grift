from setuptools import find_packages, setup

package_name = 'grift'

setup(name=package_name,
      version='0.7.0',
      description='A clean approach to app configuration',
      keywords='app config configuration schema python',
      maintainer_email='grift-maintainer@kensho.com',
      url='https://github.com/kensho-technologies/grift',
      packages=find_packages(),
      package_data={package_name + '.tests': ['*.json']},
      install_requires=[
          'schematics==1.1.1',
          'requests>=2.13.0',
          'six==1.11.0',
      ],
      )
