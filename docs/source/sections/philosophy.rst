=================
PCF Philosophy
=================


Reduced Infrastructure Operations Burden
----------------------------------------
A core principle of PCF is to automate as much of the operations burden as possible. This is done by writing out
the entire infrastructure as code and tie this code the application. Therefore changes can easily be tested before deploying
or moving to another environment. Furthermore, if the application unexpectedly dies it is easy to revert back to a working version
of not only the application but the infrastructure as well. See the section on Just in Time Infrastructure for more in depth
explication.


Customizable
-------------
There are other IAC options out there, but many times users are limited by what they can do and any customization requires
digging and editing deep in the source code. We built PCF in python with the idea of easily customizing and overriding any functions
allowing the user to do complex and unique actions if they would like.


Standardize Cloud resources
---------------------------
PCF was build with the idea that all cloud resources follow the same basic lifecycles. This makes is much easier to manage
complex deployments with resources that may have many different dependencies. We treat dependencies as a graph ensuring resources
are both deployed and terminated in the correct sequence.

Sharable
--------
There are many examples written in other IAC options, but often times duplicating the examples can be difficult and requires
time to find all the modules and dependencies. We build PCF in a way to make it very easy to share and even expand on what other
users have built.
