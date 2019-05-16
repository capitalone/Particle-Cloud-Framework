from pcf.particle.cross_cloud.docker.docker_image import DockerImage
import os
import logging

logging.basicConfig(level=logging.DEBUG)

for handler in logging.root.handlers:
    handler.addFilter(logging.Filter('pcf'))


dir_path = os.path.dirname(os.path.realpath(__file__))

image_def = {
    "pcf_name": "pcf-example",
    "flavor": "docker_image",
    "docker_resource": {
        "custom_config":{
        "auto_tag": True
        },
        "image": "anovis10/test",
        "build_params": {
            "path": dir_path
        }
    }
}

p = DockerImage(image_def)
p.set_desired_state("running")
print(p.apply())
print(p.state)
print(p.current_state_definition)
# sha256: 0cf7cfc10ce83ee1f3ac556877b35d76149d18f9c55417c689ceb60c65bb1b15
# print(p.test())
# print(p.get_latest_hash())

# print(p.get_status())
