# PCF-Flask-API
- The purpose of this example is to show one of multiple ways to use Particle Cloud Framework (PCF) to deploy cloud infrastructure which in this case is using a Flask api. In this particular example we deploy the ec2-route53 quasiparticle which creates a route53 record and adds the desired number on ec2 instances to the record set. To use in your environment, simply change some of the configurations parameters in the quasiparticle definition.



##

Interact with Flask App Locally using Docker
------------

`docker build -t pcf_flask_api .`

`docker run -it -p 5000:5000 pcf_flask_api `


Run Flask App Locally with Docker
------------
Once we have the flask app running locally, we can hit the endpoint to spin up the quasiparticle. 
First, set the desired configuration in pcf_example_config.json file.

To spin up the ec2-route53 quasiparticle with the desired configuration:

`curl -X POST http://localhost:5000/pcf`


To get the state of the ec2-route53 quasiparticle:

`curl -X GET http://localhost:5000/pcf`


To spin down the ec2-route53 quasiparticle:

`curl -X DELETE http://localhost:5000/pcf`


To do an update, make a POST request after setting the new desired configuration:

`curl -X POST http://localhost:5000/pcf`
