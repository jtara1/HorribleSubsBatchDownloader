from setuptools import setup, find_packages
import re
from os.path import join, dirname, basename, abspath


__doc__ = """This template setup.py file was intended to be generic enough
for use in any of my python modules on github. It will create setup.cfg and  
update the metadata that is required there. It'll automatically determine the 
name of the module by using the parent folder name of this setup.py file.
It pulls the text inside the README.md or README.rst to use in the 
long_descriptiion of the setup function
Fill out the information below with your own for your module.
The version 

Author: https://github.com/jtara1
Source: 
https://github.com/jtara1/misc_scripts/blob/master/misc_scripts/templates/setup.py
"""

# -------------- Update the following variables --------------- #
github_user = 'jtara1'
author = 'James T'
author_email = 'jtara@tuta.io'
description = 'Download animes from HorribleSubs'
# ------------------------------------------------------------- #

# path to this file but not including this file
directory = dirname(abspath(__file__))
# get module name from parent folder name
# assumes the parent folder (repository name) is the same as the module name
module_name = basename(directory)
github_url = 'https://github.com/{}/{}'.format(github_user, module_name)


# ------------------------ functions -------------------------- #
def create_setup_cfg(callback=None):
    """Creates the setup.cfg file with basic metadata and calls the callback"""
    with open(join(directory, 'setup.cfg'), 'w') as config:
        config.write(
            "[metadata]\nname = {module_name}\ndescription-file = {readme}"
            .format(module_name=module_name, readme=readme))
    if callback is not None:
        callback()


def change_rst_to_md_extension_in_cfg():
    """Replaces README.rst with README.md in setup.cfg"""
    try:
        with open(join(directory, 'setup.cfg'), 'r+') as config:
            text = config.read()
            text = re.sub('README.rst', 'README.md', text)
            config.seek(0)
            config.write(text)
    except (FileNotFoundError, FileExistsError):
        create_setup_cfg(change_rst_to_md_extension_in_cfg)


def get_install_requirements():
    """Returns the parsed list of strings of required modules listed in
    requirements.txt"""
    requirements = []
    try:
        with open(join(directory, 'requirements.txt'), 'r') as req_file:
            for line in req_file:
                requirements.append(re.sub("\s", "", line))
    except (FileExistsError, FileNotFoundError):
        print('[setup.py] Note: No requirements.txt found')
    return requirements


def update_cfg_module_name():
    """Replaces the module name in setup.cfg with module_name"""
    try:
        with open(join(directory, 'setup.cfg'), 'r+') as config:
            text = config.read()
            text = re.sub('name = module_name(_setup_cfg)?',
                          'name = {}'.format(module_name),
                          text)
            config.seek(0)
            config.write(text)
    except (FileNotFoundError, FileExistsError):
        create_setup_cfg(update_cfg_module_name)
# -------------------------------------------------------------- #


# Store text from README.rst or README.md to use in long description and
# update setup.cfg to point to the correct readme if needed
try:
    with open(join(directory, 'README.rst')) as f:
        readme_file_name = 'README.rst'
        readme = f.read()
except (FileNotFoundError, FileExistsError):
    try:
        with open(join(directory, 'README.md')) as f:
            readme_file_name = 'README.md'
            readme = f.read()
            change_rst_to_md_extension_in_cfg()
    except (FileExistsError, FileNotFoundError):
        readme = description

update_cfg_module_name()

setup(use_scm_version={'root': directory},
      setup_requires=['setuptools_scm'],
      name=module_name,
      packages=find_packages(),  # find all dependencies for this module
      description=description,
      long_description=readme,
      author=author,
      author_email=author_email,
      url=github_url,
      keywords=[],
      # include this if you want this module to have a command line interface
      entry_points={
          'console_scripts':
              ['hsbd={}.__main__:main'.format(module_name)]},
      install_requires=get_install_requirements(),
      # list of strs https://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[]
      )
