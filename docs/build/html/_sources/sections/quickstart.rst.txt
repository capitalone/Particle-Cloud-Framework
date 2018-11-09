=================
User Quickstart
=================


Installation
------------

To install particle cloud framework, open an interactive shell and run:

.. code::

    pip install pcf


Import and use a pcf Particle
-------------------------------

First import the particles you will use. These can be core particles or custom particles that you created.

.. code::

    from pcf.core.ec2.ec2_instance import EC2Instance
    from pcf.core import State

Next we need to pass the desired state definition to the particle.

.. code::

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

Now to start the ec2 instance using pcf simply initialize the particle and set the desired state to running and apply.

.. code::

    particle = EC2Instance(ec2_example_definition)

    particle.set_desired_state(State.running)
    particle.apply()

To terminate simply change the desired state to terminated and apply.

.. code::

    particle.set_desired_state(State.terminated)
    particle.apply()


.. seealso:: `PCF particle and quasiparticle examples <TODO/pcf/pcf-examples>`_

