# What is Just in Time Infrastructure
Just in Time Infrastructure (JiTI) is a deployment model in which the entire infrastructure required for an application is written in code and deployed with the same life cycles alongside
the application. Check our docs for more infomation on JiTI and the benifits this provides.

# What does this example do?
- This example deploys an ec2 (application layer) alongside all required infrastructure pieces and then proceeds to terminate them all. This example requires no configuration
to start (only an aws account with access to provision resources) and deploys vpc, subnet, security group, instance profile, and ec2. This example can be expanded to any
application which would then be able to be deployed and shared easily without configuration changes.

