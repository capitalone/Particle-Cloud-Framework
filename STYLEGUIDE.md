# Particle Cloud Framework Style Guide

This is a Python Style Guide for the PCF Framework. The intent of this guide is to strive for cleaner and better code quality. Following this guide, our code will be approachable to anyone who needs to maintain it later, including ourselves!

## Table of Contents
1. [Virtual Environments](#venv)
2. [Imports](#imports)
3. [Naming](#naming)  
    i. [Variables](#variables)  
    ii. [Class names](#classes)  
    iii. [Functions/Methods](#funcs)
4. [Spacing](#spacing)
5. [Strings](#strings)  
    i. [Quotes](#quotes)  
    ii. [Docstrings](#docstr)
6. [Dictionary Key Value Retrieval](#dict)
7. [PCF Utility Functions](#pcf_util)
8. [PCF Exceptions](#pcf_excep)

## <a name="venv">Virtual Environments</a>
------
### Conda
Conda is a package management system that can help you easily keep track of the package requirements 
for projects and install them automatically for you. 
You can set up and share collections of packages called environments.

For sake of clarity, all references will be intended for MacOS users. 

#### Installation
Visit this <a href="https://docs.anaconda.com/anaconda/install/">link</a> to 
find installation details for your appropriate OS.

<a href="https://www.anaconda.com/download/#macos"> MacOs</a>  

Click *version 3.7*

### Create a new virtual env
Visit this 
<a href="https://conda.io/docs/user-guide/getting-started.html#starting-conda">link</a> 
to find documentation on your appropriate OS.

All conda commands will be typed in the Terminal window.

```commandline
conda create --name pcf-local python==3.6
```

*PCF requires Python version 3.6+*

### Activate virutal env
```commandline
source activate pcf-local
```

### Deactivate virtual env
```commandline
source deactivate
```

### View list of exisiting virtual envs
```commandline
conda info --envs
```

## <a name="imports">Imports</a>
------
Refrain importing entire modules when only 1 object from the module is needed.

**Don't:**
```python
import boto3, json, logging
import pcf.core.PCF_exceptions 
```

**Do:**
```python
import boto3
import json
import logging

from pcf.core.pcf_exceptions import NoResourceException
```

## <a name="naming">Naming</a>
------
PCF typically follows the same naming conventions as <a href="https://visualgit.readthedocs.io/en/latest/pages/naming_convention.html">PEP8 standards</a>.

### <a name="variables">Variables</a>  
```python
# Lowercase multi-word separated by an underscore
my_greeting = "hello"
```

```python
# Non-public instance variables should begin with a single underscore
_client = ""
```

### <a name="classes">Classes</a>
```python
# UpperCaseCamelCase convention
class LambaFunction():
    # class

class AWSResource():
    # class

class EC2Instance():
    # class
```

### <a name="funcs">Fucntions/Methods</a>
```python
# Lowercase multi-word separated by an underscore
def get_status(self):
    pass
```
```python
# Non-public methods should begin with a single underscore
def _terminate(self):
    pass
```

## <a name="spacing">Spacing</a>
------
* 4 spaces = 1 indent
* Leave a single blank line after function/method declarations to aid in visual clarity and organization

## <a name="strings">Strings</a>
------
### <a name="quotes">Quotes</a>  

    In Python single quotes and double quotes are used interchangablely. We will stick to double quotes for consistency.  

**Don't:**  
```python
nameOfSchool = 'Marshall'
nameOfOffice = "Clarendon"
```  

**Do:**  
```python
nameOfSchool = "Marshall"
nameOfOffice = "Clarendon"
```   

### <a name="docstr">Docstrings</a>  
Docstrings act as documentation for method definitions of a class within PCF. Always use """triple double quotes""" around docstrings. For multi-line docstrings, place the closing qoutes on a line by itself.

The docstrings should give a brief description of what the method/class is doing, explain arguments and their type, if any, and list what the method/class returns.

For more info see the <a href="https://www.python.org/dev/peps/pep-0257/#what-is-a-docstring">docs</a>.

**Example:**
```python
def is_state_equivalent(self, state1, state2):
    """
    Determines if states are equivalent. Uses equivalent_states defined in the Glacier class.

    Args:
        state1 (State):
        state1 (State):

    Returns:
        bool
    """
```

## <a name="dict">Dictionary Key Value Retrieval</a>
------
**Don't:**
```python
self.bucket_name = self.desired_state_definition["Bucket"]
```
**Do:**
```python
# dict.get("Key", default=None)
bucket_name = desired_state_definition.get("Bucket")
```

## <a name="pcf_util">PCF Utility Fucntions</a>
There are several functions in <a href="https://github.com/capitalone/Particle-Cloud-Framework/blob/master/pcf/util/pcf_util.py">pcf_util.py</a>
that perform various tasks such as creating a dictionary passed on a key set and finding nested values in a dictionary.
Refer to this module when performing such complex operations. If there is not an existing function that meets your needs, simply
create one. The desired functions are then imported into the particular module you are implementing.

Example:
```python
def param_filter(curr_dict, key_set, remove=False):
    """
    Filters param dictionary to only have keys in the key set
    Args:
        curr_dict (dict): param dictionary
        key_set (set): set of keys you want
        remove (bool): filters by what to remove instead of what to keep
    Returns:
        filtered param dictionary
    """
    if remove:
        return {key: curr_dict[key] for key in curr_dict.keys() if key not in key_set}
    else:
        return {key: curr_dict[key] for key in key_set if key in curr_dict.keys()}
```

## <a name="pcf_excep">PCF Exceptions</a>
There are several exceptions in <a href="https://github.com/capitalone/Particle-Cloud-Framework/blob/master/pcf/core/pcf_exceptions.py">pcf_exceptions.py</a>
that define various exceptions. Refer to this module when considering exception handling. If there is not an existing exception that meets your needs, simply
create one. The desired exceptions are then imported into the particular module you are implementing.

Example:
```python
class NoCodeException(Exception):
    def __init__(self):
        Exception.__init__(self, "Did not provide local zipfile or zipfile location in S3")
```
