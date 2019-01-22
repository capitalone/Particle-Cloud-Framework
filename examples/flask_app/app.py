import json
import pcf

from flask import Flask, request
from pcf.core import State
from pcf.quasiparticle.aws.ec2_route53.ec2_route53 import EC2Route53

app = Flask(__name__)

#We read the json configuration of our desired quasiparticle
with open('pcf_example_config.json', 'r') as f:
    pcf_config = json.load(f)

#Here we initialize the desired state definitions
ec2_route53_quasiparticle.set_desired_state(State.running)

#GET /pcf endpoint returns the current state of our EC2 Route53 Quasiparticle
@app.route('/pcf', methods=['GET'])
def get_pcf_status():
    return str(ec2_route53_quasiparticle.get_state())

#POST /pcf endpoint creates the EC2 Route53 Quasiparticle with the desired configuration
@app.route('/pcf', methods=['POST'])
def create():
    ec2_route53_quasiparticle.set_desired_state(State.running)

    if request.data:
        payload = json.loads(request.data)
        multiplier = payload.get('ec2_multiplier')
        pcf_config['particles'][0]['multiplier'] = multiplier
        ec2_route53_quasiparticle = EC2Route53(pcf_config)

    try:
        ec2_route53_quasiparticle.apply(sync=True)
    except Exception as e:
        raise e

    return str(ec2_route53_quasiparticle.get_state())

#DELETE /pcf endpoint deletes the EC2 Route53 Quasiparticle
@app.route('/pcf', methods=['DELETE'])
def delete():
    ec2_route53_quasiparticle.set_desired_state(State.terminated)

    try:
        ec2_route53_quasiparticle.apply(sync=True)
    except Exception as e:
        raise e

    return str(ec2_route53_quasiparticle.apply(sync=True))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')