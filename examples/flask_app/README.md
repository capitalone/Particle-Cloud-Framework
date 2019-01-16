# PCF-Flask-API
The purpose of this app is to show how to use PCF in a Flask api to spin up cloud resources. In this particular example we will utilize Capital One's Particle Cloud Framework to deploy ec2-route53 quasiparticle.


##

Run Flask App Locally with Docker
------------

`docker build -t pcf_flask_api .`

`docker run -it -p 5000:5000 pcf_flask_api `


Run Flask App Locally with Docker
------------
Once we have the flask app running locally, we can hit the endpoint to spin up the quasiparticle. 
First, set the desired configuration in higgs_example_config.json file.

To spin up the ec2-route53 quasiparticle with the desired configuration:

`curl -X POST http://localhost:5000/higgs`


To get the state of the ec2-route53 quasiparticle:

`curl -X GET http://localhost:5000/higgs`


To spin down the ec2-route53 quasiparticle:

`curl -X DELETE http://localhost:5000/higgs`


To do an update, make a POST request after setting the new desired configuration:

`curl -X POST http://localhost:5000/higgs`
