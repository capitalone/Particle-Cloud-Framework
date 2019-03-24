===========================
Developer Quickstart
===========================


Creating a new Particle
---------------------------------------

To learn more about particles and quasiparticle check out the pcf framework part of the docs.
From that you should now know that particles are essential cloud resources that map to the states
and lifecycle. To create a new particle all you have to do is inherit the base particle class and
implement the transition functions and sync state function which is how the particle figures out the
current state. Sometimes helper functions are needed for the more complex particles. Feel free to check
out our repository of premade particles and after you create your own feel free to submit a pr with the new
particle, docstrings, and tests.


This is an example of how to create a new aws particle.

.. code::

    from pcf.core.aws_resource import AWSResource
    from pcf.util import pcf_util
    import logging
    import json

    logger = logging.getLogger(__name__)


    class NewAwsParticle(AWSResource):

        flavor='new_particle'

        #this is helpful if the particle doesn't have all three states or has more than three.
        equivalent_states = {
                State.running: 1,
                State.stopped: 0,
                State.terminated: 0,
            }
        super(NewAwsParticle, self).__init__(particle_definition, 'new_particle')


That is the standard initial setup. Now the functions that you have to implement

.. code::

        def sync_state(self):
            #implement

        def _terminate(self):
            #implement

        def _start(self):
            #implement

        def _stop(self):
            #implement

        def _update(self):
            #implement if needed



Extend functionality of a Particle
---------------------------------------

The power of pcf comes from its extensibility. All particle functionality can be overwritten and custom functions can be added.

This is an example of how to add a function that adds a security group to a running ec2. This new particle can be now be imported by anyone
else who also wants this additional functionally.

.. code::

    from pcf.core.ec2.ec2_instance import EC2Instance


    class EC2Extended(EC2Instance):
        flavor = "ec2_extended"

        def __init__(self, particle_definition):
            super(EC2Extended, self).__init__(particle_definition)

        def add_security_group(self, security_group_id):
            all_security_groups = self.current_state_definition["SecurityGroupIds"]
            all_security_groups.append(security_group_id)
            self.client.modify_attribute(Groups=all_security_groups)

To use this new functionality you import the extended particle and call the function.

.. code::

    import EC2Extended

    # same config as before

    particle = EC2Extended(ec2_example_definition)

    particle.add_security_group("SG-123456")



Create a Quasiparticle
---------------------------------------

A quasiparticle is a collection of particles that have custom dependencies on each other. They follow the same state lifecycles as particles
so can be imported and extended the same way and simplify the provisioning and maintenance of complex infrastructure deployments.
For example, we can create a basic quasiparticle that has a cluster of master and worker nodes. We want all of the cluster nodes to be running
before any of the worker nodes would spin up. We would handle this by created a custom config var that we can use in our custom
quasiparticle definition and create a function that sets the parents of each worker particle.


.. code::

    from pcf.core.ec2.ec2_instance import EC2Instance
    from pcf.core.quasiparticle import Quasiparticle

    class DistributedMasterWorker(Quasiparticle):
        flavor = 'distributed_master_worker'

        def __init__(self, particle_definition):
            super(DistributedMasterWorker, self).__init__(particle_definition)
            self.master = self.particle_definition['custom_config'].get('master')
            self.set_parents()

        def set_parents(self):
                """
                Checks for the master ec2 instances and adds them as a parent to all other ec2 particles.
                """
                ec2_particles = self.pcf_field.get_particles(flavor="ec2_instance")
                ec2_masters = [ec2_particles[ec2_name] for ec2_name in ec2_particles.keys() if self.master in ec2_name]
                for ec2_name in ec2_particles:
                    if self.master not in ec2_name:
                        self.pcf_field.particles["ec2_instance"][ec2_name].parents.update(list(ec2_masters))

                self.pcf_field.link_particles(self.pcf_field.particles)


To use this quasiparticle we simple import, initialize the desired state definitions, set the desired start, and apply.

.. code::

    import DistributedMasterWorker

    kafka_zookeeper_example_definition = {
        "pcf_name": "example",
        "flavor": "distributed_master_worker",
        "custom_config": {
            "master":"master-ec2",
        },
        "particles":[
        {
            "flavor": "ec2_instance",
            "pcf_name": "master-ec2",
            "multiplier":3,
            "aws_resource": {
                "custom_config": {
                    "instance_name": "pcf-master",
                    ...
                },
                ...
            }
        },
        {
            "flavor": "ec2_instance",
            "pcf_name": "worker-ec2",
            "multiplier":3,
            "aws_resource": {
                "custom_config": {
                    "instance_name": "pcf-worker,
                    ...
                },
                ...
            }
        }
        ]
    }

    quasiparticle = DistributedMasterWorker(kafka_zookeeper_example_definition)

    quasiparticle.set_desired_state("running")
    quasiparticle.apply()

