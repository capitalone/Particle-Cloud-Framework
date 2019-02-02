import pytest

test_cft =  {
    "Ec2Instance" : {
        "Type" : "AWS::EC2::Instance",
        "Properties" : {
            "ImageId" : { "Fn::FindInMap" :["Arch" ] },
            "KeyName" : { "Ref" : "KeyName" },
        }
    },
    "Ec2Instance2" : {
        "Type" : "AWS::EC2::Instance",
        "DependsOn" : "Ec2Instance",
        "Properties" : {
            "KeyName" : { "Ref" : "KeyName" },
        }
    }
}


tests = [
    (test_cft,)

]

@pytest.mark.parametrize("definition,result,class", values, ids=list(testdata.keys()))
def test_apply(definition, updated_definition, test_tag):
