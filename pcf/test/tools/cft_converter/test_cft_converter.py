import pytest

test_cft =  {
    "Ec2Instance" : {
        "Type" : "AWS::EC2::Instance",
        "DependsOn" : "test",
        "Properties" : {
            "ImageId" : { "Fn::FindInMap" :["Arch" ] },
            "KeyName" : { "Ref" : "KeyName" },
            "InstanceType" : { "Ref" : "InstanceType" },
            "SecurityGroups" : [{ "Ref" : "Ec2SecurityGroup" }],
            "BlockDeviceMappings" : [
                {
                    "DeviceName" : "/dev/sda1",
                    "Ebs" : { "VolumeSize" : "50" }
                },{
                    "DeviceName" : "/dev/sdm",
                    "Ebs" : { "VolumeSize" : "100" }
                }
            ]
        }
    }
}

@pytest.mark.parametrize("definition,result,class", values, ids=list(testdata.keys()))
def test_apply(definition, updated_definition, test_tag):
