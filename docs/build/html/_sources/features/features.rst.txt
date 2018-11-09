================================
Advanced Configuration Features
================================

Documentation of current Particle Cloud Framework features

* :ref:`multiplier`
* :ref:`inherit`
* :ref:`baseconfig`
* :ref:`lookup`
* :ref:`callback`
* :ref:`protection`
* :ref:`rollback`


.. _multiplier:

Multiplier
------------

The multipler lets you easily create multiple instances of the same resource. This can be used in any quasiparticle and
will create copies of the same particle with the unique keys being indexed from '-0' to whatever multiplier you specify.

This is an example of how to use multipler to create 3 ec2 instances with names `multi-name-0` , `multi-name-1` , `multi-name-2`

.. code::

    quasiparticle_definition = {

        "pcf_name":"multi_ec2",
        "flavor":"quasiparticle",
        "particles":[
            {
                "flavor":"ec2_instance",
                "multiplier":3
                "aws_resource": {
                    ...
                    custom_config:{
                        "instance_name":"multi-name"
                    }
                }
            }
    }

.. _inherit:

Inherit Parent Variables
------------------------

In quasiparticles some particles may require certain variables from their parents to run. Variables can be dynamically passed to a parent's
child by using the notation "$inherit$particle_type:pcf_name$variable." Any variable that in the parent's current definition can be passed. If it
is a nested variable then you can use '.' to signify nested. For example "variable.nested_variable"

For example a PrivateIpAddress can be passed to the child's userdata as a param.

.. code::

     example_definition = {
         "pcf_name": "pcf-example",
         "flavor": "distributed_master_worker",
         "particles":[{
             "flavor": "ec2_instance",
             "pcf_name": "parent-ec2",
             "aws_resource": {
                 ...
             }
         },
         {
             "flavor": "ec2_instance",
             "pcf_name": "child-ec2",
             "aws_resource":{
                 "custom_config": {
                     ...

                     "userdata_params": {
                         "parentIP":"$inherit$ec2_instance:parent-ec2$PrivateIpAddress"
                     }

                 },
             }
         }
         ]
     }


.. _baseconfig:

Base Config
------------

If you have similar particles with only a few differences in a quasiparticle, you can use the base_particle_config flag to grab all configurations
from another particle already defined in the quasiparticle. This flag takes in the pcf_name of the base particle.

For example, if you have multiple ec2 instances, but what them to share the same sg's but want to change the instance size,
you can use the flag and only override the instance param.

.. code::

     example_definition = {
         "pcf_name": "pcf-example",
         "flavor": "distributed_master_worker",
         "particles":[{
             "flavor": "ec2_instance",
             "pcf_name": "base-ec2",
             "aws_resource": {
                 ...

                 "InstanceType": "t2.nano",
                 "KeyName": "key",
                 "SecurityGroupIds": [
                     "sg-abcd1234",
                     "sg-abcd2345",
                 ],
                 "SubnetId": "subnet-abdc1234",
             }
         },
         {
             "flavor": "ec2_instance",
             "pcf_name": "child-ec2",
             "base_particle_config": "base-ec2",
             "aws_resource":{
                 ...

                 "InstanceType": "m3.medium",
             }
         }
         ]
     }


.. _lookup:

Lookup
------------

Lookup allows you to get id's for resources by their names. In the particle definition, set the value of the id field to "$lookup$(resource type)$(resource names)"

When there is a list of names (security groups), separate them using ':'

As of now only an AWS lookup for SnapshotId, ResourceName, ImageId, SecurityGroupIds, Ami, and SubnetId are implemented.

For Ami, either "instance-profile" or "role" must be set in the (resource names) and appended by ':' and name.

.. code::

    particle_definition = {
        "pcf_name": "pcf-example",
        "flavor": "ec2_instance",
        "aws_resource": {
            "custom_config":{
                "instance_name": "gg-instance",
            },
            "BlockDeviceMappings": [
                {
                    "Ebs": {
                        "SnapshotId": "$lookup$snapshot$ami-build"
                    }
                }
            ],
            "InstanceType": "m4.large",
            "KeyName": "secret-key",
            "MaxCount": 1,
            "MinCount": 1,
            "SecurityGroupIds": "$lookup$security_groups$test_sg:test_sg2",
            "SubnetId": "$lookup$subnet$public",
            "IamInstanceProfile": {
                "Arn": "$lookup$iam$instance-profile:InstanceProfile-Default"
            },
            "InstanceInitiatedShutdownBehavior": "stop",
            "tags": {
                "Test": "Tag"
            }
        }
    }


.. _callback:

Callback
------------

Callbacks can be used to run a function after a state transition is triggered.

Parameters are passed to the function as a dictionary, as shown in the example

.. code::

    def example_start_callback():
        print("callback triggered after start")


    def example_terminate_callback(text):
        print(text)

    ec2_instance_example_json = {
        "pcf_name": "ec2-example",
        "flavor": "ec2_instance",
        "callbacks": {
            "start": {"function": example_start_callback},
            "terminate": {"function": example_terminate_callback, "kwargs": {"text": "terminate"}}
         }
     }


.. _protection:

Termination Protection
----------------------

Termination protection is a flag that can be set for particles in a quasipaerticle. This allows for you to set the desired
state of the quasiparticle to terminated and get to that state while still having resources you need to be persisted. For example,
you may have a db as a parent and want terminate all other particles. You can set the termination protection flag to true for the
db particle and then simply terminate the quasiparticle.

.. code::

          example_definition = {
              "pcf_name": "persist_rds_example",
              "flavor": "quasiparticle",
              "particles":
              [
                  {
                      "flavor": "rds_instance",
                      "pcf_name": "rds-persist",
                      "persist_on_terminate": True,
                      "aws_resource": {
                          ...
                      }
                  },
                  {
                      "flavor": "ec2_instance",
                      "pcf_name": "child-ec2",
                      "aws_resource":{
                          ...
                       }
                  }
              ]
          }


.. _rollback:

Rollback
------------

You can set the rollback flag to True when calling a quasiparticle apply, this will trigger if a particle fails to provision and
will terminate all previously created particles. Rollback is set to False by default.

.. code::

    rollback_quasiparticle.apply(rollback=True)

