from pcf.particle.aws.glacier.glacier_vault import GlacierVault

# Edit example json to work in your account
glacier_example_json = {
    "pcf_name": "pcf_glacier",
    "flavor": "glacier",
    "aws_resource": {
        "vaultName": "pcf_test_glacier", # Required
        "custom_config": {
            "Tags": {
                "Name":"pcf-glacier-example"
            }
        }
    }
}

# create Glacier particle
glacier_particle = GlacierVault(glacier_example_json)

# example start
glacier_particle.set_desired_state("running")
glacier_particle.apply()

print(glacier_particle.get_state())

# show tags
if glacier_example_json.get("aws_resource").get("custom_config").get("Tags"):
    tags = glacier_particle.client.list_tags_for_vault(
            vaultName=glacier_particle.vault_name
        )
    print("Tags: ", tags.get("Tags"))

# example terminate
glacier_particle.set_desired_state("terminated")
glacier_particle.apply()

print(glacier_particle.get_state())
