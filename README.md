# Due to changes in the priorities, this project is currently not being supported. The project is archived as of 9/17/21 and will be available in a read-only state. Please note, since archival, the project is not maintained or reviewed. #

[![Build Status](https://img.shields.io/travis/capitalone/Particle-Cloud-Framework/master.svg?label=master)](https://travis-ci.org/capitalone/Particle-Cloud-Framework)
[![Build Status](https://img.shields.io/travis/capitalone/Particle-Cloud-Framework/develop.svg?label=develop)](https://travis-ci.org/capitalone/Particle-Cloud-Framework)
[![Licence](https://img.shields.io/badge/license-Apache%202-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![PyPi Version](https://img.shields.io/pypi/v/pcf.svg?maxAge=2592000)](https://pypi.org/project/pcf/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/pcf.svg?label=Python)](https://pypi.org/project/pcf/)


# Particle Cloud Framework

Particle Cloud Framework is a cloud resource provisioning framework that is fully customizable and extensible, callable by code, and does not require manually maintaining states of resources. Particle Cloud Framework enables the standardization of modeling hierarchical cloud infrastructure, automating deployments, and managing lifecycles of cloud resources.

## Docs

[Docs](https://capitalone.github.io/Particle-Cloud-Framework/docs/build/html/index.html) including quickstart and developer guide

##

Installation
------------

To install particle cloud framework, open an interactive shell and run:

`pip install pcf`


Import and use a PCF Particle
-------------------------------

First import the particles you will use. These can be core particles or custom particles that you created.
See examples if you need help creating your config.

```
from pcf.core.ec2.ec2_instance import EC2Instance
```

Next we need to pass the desired state definition to the particle.

```
    ec2_example_definition = {
        "pcf_name": "ec2_example",
        "flavor":"ec2",
        "aws_resource": {
            "ImageId": "ami-xxxxx",
            "InstanceType": "t2.micro",
            "KeyName": "secret-key-xxx",
            "SecurityGroupIds": [
              "sg-xxxxxx",
            ],
            "SubnetId": "subnet-xxx",
            "userdata_template_file": "userdata-script-xxxxx.sh",
            "userdata_params": {},
            "IamInstanceProfile": {
              "Arn": "arn:aws:iam::xxxxxxxxx"
            },
            "InstanceInitiatedShutdownBehavior": "stop",
            "tags": {
              "NAME":"Value"
            },
            "BlockDeviceMappings": [
              {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                  "DeleteOnTermination": true,
                  "VolumeSize": 20,
                  "VolumeType": "gp2"
                }
              }
            ]
          }
    }
```

Now to start the ec2 instance using pcf simply initialize the particle and set the desired state to running and apply.


```
    particle = EC2Instance(ec2_example_definition)

    particle.set_desired_state('running')
    particle.apply()
```


To terminate simply change the desired state to terminated and apply.


```
    particle.set_desired_state('terminated')
    particle.apply()
```

## Published Content

[*Just in Time Cloud Infrastructure:
Redefining the Relationship Between Applications and Cloud Infrastructure*](https://www.capitalone.com/tech/cloud/just-in-time-cloud-infrastructure)


## Supported Cloud Services

[Particles](https://capitalone.github.io/Particle-Cloud-Framework/docs/build/html/particlelist.html)

[Quasiparticles](https://capitalone.github.io/Particle-Cloud-Framework/docs/build/html/quasiparticlelist.html)

## Development Setup
To develop locally, clone this project and ensure you have the Invoke package installed globally via `pip` or `conda`:
```
$ pip install invoke
```

or

```
$ conda install invoke
```

Then you can use the project management tasks defined in `tasks.py` via the `invoke` CLI:
```
$ invoke --list
Available tasks:

  build      Build PCF with the PCF_TAG value given or the VERSION in pcf/__init__.py
  docs-add   Run sphinx-apidoc on pcf and pcf/test
  lint       Run pylint on pcf directory
  publish    Publish package to Pypi
  setup      Setup a virtualenv, activate it, and install requirements
  test       Run pytest on pcf directory, generating a coverage report

$ invoke setup && source venv/bin/activate
$ invoke test
```
## RoadMap

[Roadmap](https://capitalone.github.io/Particle-Cloud-Framework/docs/build/html/sections/roadmap.html)


## Contributors

We welcome Your interest in Capital One’s Open Source Projects (the
“Project”). Any Contributor to the Project must accept and sign an
Agreement indicating agreement to the license terms below. Except for
the license granted in this Agreement to Capital One and to recipients
of software distributed by Capital One, You reserve all right, title,
and interest in and to Your Contributions; this Agreement does not
impact Your rights to use Your own Contributions for any other purpose.

[Sign the Individual Agreement](https://docs.google.com/forms/d/19LpBBjykHPox18vrZvBbZUcK6gQTj7qv1O5hCduAZFU/viewform)

[Sign the Corporate Agreement](https://docs.google.com/forms/d/e/1FAIpQLSeAbobIPLCVZD_ccgtMWBDAcN68oqbAJBQyDTSAQ1AkYuCp_g/viewform?usp=send_form)


## Code of Conduct

This project adheres to the [Open Code of Conduct](https://developer.capitalone.com/resources/code-of-conduct)
By participating, you are
expected to honor this code.

