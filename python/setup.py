from setuptools import setup

setup(
    name='werewolf',
    version='0.7',
    packages=['discord', 'schedule', 'cipher'],
    package_dir={'': 'python'},
    url='https://github.com/nvsneddon/werewolf',
    license='MIT',
    author='Nathaniel',
    author_email='nathaniel.sneddon@gmail.com',
    description='A Discord Bot that runs a game of real-time werewolf'
)
