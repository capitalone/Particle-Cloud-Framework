=================
Using the PCF CLI
=================

Installation
------------

The CLI is packaged in the PCF Python package, so after running

.. code::

    pip install pcf

you should be able to execute the CLI from your command line provided your
Pip packages are available in your $PATH:

.. code::

    $ pcf -h
    Usage: pcf [--version] [--help] <command> [<args>...]

    Particle Cloud Framework

    Options:
    -v, --version  Show PCF version.
    -h, --help     Show this message and exit.

    Commands:
    apply      Set a desired state and apply changes
    run        Set desired state to 'run' and apply changes
    stop       Set desired state to 'stopped' and apply changes
    terminate  Set desired state to 'terminated' and apply changes

Usage
-----

By default, the CLI reads Particle and Quasiparticle definitions from a JSON file named
`pcf.json` or a YAML file named `pcf.yml` located in the current working directory.

The following `pcf.json` file defines a new AWS KMS key Particle and accepts the same top-level
fields that Particle and Quasiparticle definitions use in the PCF Python library:

.. code::

    {
        "pcf_name": "kms_example",
        "flavor": "kms_key",
        "aws_resource": {
            "Description": "an example key",
            "Tags": [
                {
                    "TagKey": "InUse",
                    "TagValue": false
                }
            ],
            "custom_config": {
                "key_name": "pcf_kms_example"
            }
        }
    }

An equivalent `pcf.yml` file would look like the following:

.. code::

    ---
    pcf_name: kms_example
    flavor: kms_key
    aws_resource:
      Description: an example key
      Tags:
        - TagKey: InUse
          TagValue: false
      custom_config:
        key_name: pcf_kms_example

With this pcf.json file, you can run

.. code::

    $ pcf run kms_example

and PCF will run the `kms_key` Particle flavor's `apply` method and set the desired state
of your Particle to `running`.

You can then perform subsequent actions on the Particle's state:

.. code::

    $ pcf stop kms_example
      ...

    $ pcf terminate kms_example
      ...

Using a Custom Config File Name
-------------------------------

If you would like to name your config files something besides `pcf.json` or `pcf.yml`,
specify the relative path to your file using the `--file` or `-f` option to any command
that sets a desired state. The file must have a valid `.json` or `.yml` file extension.

.. code::

    $ pcf run --file dev_infra.yml


Cascading Changes from the CLI
------------------------------

To instruct PCF to cascade changes when `apply` is called on your Particles or Quasiparticles,
provide the `--cascade` or `-c` flag to the CLI when invoking a command that sets a desired state:

.. code::

    $ pcf stop --cascade my_quasiparticle
