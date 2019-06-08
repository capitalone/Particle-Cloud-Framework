==========================================
Contributing to Particle Cloud Framework
==========================================


Submitting a new PR
--------------------------

We believe the value of pcf comes from the community and contributions are greatly appreciated and encouraged. Feel free
to create new branches off of develop and submit your pr. When creating new particles and quasiparticles make sure to add
docstrings to all your functions and add tests.

`PCF Github Repo <https://github.com/capitalone/Particle-Cloud-Framework>`_


Writing Tests
--------------

To add a new test for an aws particle add the test definition, updated definition, and test type to `testdata.json`.
The tests can use moto or placebo. If using placebo you will have to create a folder called replay for the specified
resource for example `sns/replay`. Then run `python generate_placebo.py TEST-NAME` with whatever you called your test name
in `testdata.json`. This creates all the required files. You can test your particle now by running
`python test_particles TEST-NAME` to make sure it passes all assertions. If you use moto make sure all the required function
calls are supported in moto and if that is the case then all you need to do is include the moto client that you wish to use
in the test json. See the other test definitions already in `testdata.json` for help starting.


Requesting New Features
--------------------------

To request new particles, quasiparticles or features submit an issue in the pcf github repo and label appropriately.


`PCF Github Issues <https://github.com/capitalone/Particle-Cloud-Framework/issues>`_


Particle Cloud Framework Docs
------------------------------

Particle Cloud Framework docs are generated using Sphinx. To test your changes to the docs locally run

.. code::

    make docs

If you want to add docs for a newly created particle then run

.. code::

    make docs-add


Point your browser to `<path/to/repo>/pcf/docs/build/html/index.html` to view your changes

