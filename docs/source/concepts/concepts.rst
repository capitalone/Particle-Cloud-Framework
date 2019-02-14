================================
Core Concepts
================================

Particle Cloud Framework is a cloud resource provisioning framework whose key
features include being fully customizable and extensible, callable by code,
and does not require manually maintaining states of resources. This unique combination
leads to new ways of thinking about cloud infrastructure and its relation to not
only applications, but software development in general.

* :ref:`jiti`


.. _jiti:

Just in Time Infrastructure
---------------------------

Just-in-time infrastructure is a model in which the entire infrastructure stack
required for an application is written as code and deployed with the same lifecycles
alongside the application. The idea for JiTI came during the development of a data
analytics platform for data scientists, many of whom wanted to use the platform with
sensitive data. Working with sensitive date made it extremely difficult to gain the
sufficient permission and access needed for the platform to be hosted in one centralized
location. Therefore, the team decided early on to design the platform to be “dropshippable”
(deployed in any cloud account with minimal to no code changes required), and simply
deploy the platform directly into any account where the data and the data scientists
were already working.

There was just one catch - the team building the platform did
not have the resources to manually configure and stand up the platform in dozens of
accounts. So, in addition to the data analytics platform, we also built a Python-based
cloud resource management framework which has recently been open-sourced by Capital One
as Particle Cloud Framework. This framework was built intentionally with JiTI in mind,
but the principles of JiTI can be applied with any programming language and framework.
Using Particle Cloud Framework, we were easily able to combine the platform codebase with
the infrastructure required to run it, making it extremely simple to scale out (in this
case on AWS, but the same can be done on any cloud provider). The infrastructure codebase
contained not only the compute and storage resources required, but all components including
the VPC, subnets, IAM roles (access permissions), and networking resources. In cases where
some of the resources had to be shared with other applications, or we did not have the
required permissions to dynamically create a resource, the resource was passed in to the
configuration programmatically. Otherwise, all resources were generated during run time.


Combining the platform with its infrastructure code is an extremely powerful concept and
ensures the required infrastructure is provisioned not only correctly, but consistently,
between development and production environments as well as across accounts. Now, when
additional features that require additional infrastructure components are ready to be deployed,
users simply update the application, which as part of the update, would also deploy the new required infrastructure.


**Benefits**

* **Application Isolation**

Tying your application and infrastructure code reduces the risk of negatively affecting other
applications and vice versa. JiTI ensures you have exactly the same infrastructure in all your
development, QA, and production environments. Furthermore, JiTI allows the infrastructure code
to be versioned directly alongside your application, enabling the deployment of various versions
at the same time with different infrastructure requirements.

* **Cost Management**

JiTI makes resource management much simpler since resources can simply be attributed to unique
applications, so there is no risk when deleting rogue or unused infrastructure. Additionally,
JiTI simplifies the deployment and tearing down your entire application, providing  cost savings
while not utilizing the application (especially for development, test, and QA environments).

* **Dropshipable**

Deploying an application and its infrastructure together in another account or environment ensures
the application works as promised.

* **Auditability**

Since the entire infrastructure is written as code alongside the application, auditing is much easier
because JiTI assumes all dependencies are in the same code base.

* **Security**

JiTI ensures that resources related to security such as networking, access control, and identity
management are deployed only when they're needed by an application. When the application gets
terminated, those vulnerable resources also get terminated reducing the security risk from leftover and outdated resources.

* **Resiliency**

JiTI makes it easy to merely recreate the entirety of the infrastructure if things go wrong, instead
of having to manually inspect what might have caused a failure and testing a fix and its potential
effects on the rest of the ecosystem.

* **Self Management**

JiTI can enable applications to manage their own infrastructure once deployed. This is useful if an
application has a variable or unpredictable workload and can automatically scale the underlying infrastructure itself.

**Considerations When Using JiTI**

* **Governance**

Since applications are now tightly coupled with the infrastructure, centralized governance teams will need to incorporate
new standards and procedures to ensure security, cost, and regulatory compliance. This can be done passively through
tools that actively scan and delete resources that are non compliant, or fine-grained access management that limits the scope of each application.

* **Permissions**

Adopting JiTI may require a new way to manage access management since application teams are deploying the entire
infrastructure stack from security rules and subnets, to compute and networking resources. One way to manage
this is to create a centralized tool that has the actual permissions to deploy, and before any deployment it could
programmatically scan the application code to enforce customized rules (for example prohibit public endpoints).



