import pytest
from tools.cft_converter.cft_converter import ConvertCFT
from copy import deepcopy

test_cft =  {
    "Ec2Instance" : {
        "Type" : "AWS::EC2::Instance",
        "Properties" : {
            "ImageId" : { "Fn::FindInMap" :"Arch"},
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

results = {
    "all":{'pcf_name': 'PCF_NAME', 'flavor': 'quasiparticle', 'particles': [{'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': [], 'aws_resource': {'ImageId': '$lookup$RESOURCE$Arch', 'KeyName': '$lookup$RESOURCE$KeyName'}}, {'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': ['PARENT_FLAVOR:Ec2Instance'], 'aws_resource': {'KeyName': '$lookup$RESOURCE$KeyName'}}]},
    "Properties":{'pcf_name': 'PCF_NAME', 'flavor': 'quasiparticle', 'particles': [{'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': [], 'aws_resource': {'ImageId': {'Fn::FindInMap': 'Arch'}, 'KeyName': {'Ref': 'KeyName'}}}, {'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': [], 'aws_resource': {'KeyName': {'Ref': 'KeyName'}}}]},
    "DependsOn":{'pcf_name': 'PCF_NAME', 'flavor': 'quasiparticle', 'particles': [{'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': [], 'aws_resource': {}}, {'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': ['PARENT_FLAVOR:Ec2Instance'], 'aws_resource': {}}]},
    "Ref":{'pcf_name': 'PCF_NAME', 'flavor': 'quasiparticle', 'particles': [{'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': [], 'aws_resource': {'ImageId': {'Fn::FindInMap': 'Arch'}, 'KeyName': '$lookup$RESOURCE$KeyName'}}, {'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': [], 'aws_resource': {'KeyName': '$lookup$RESOURCE$KeyName'}}]},
    "FindInMap":{'pcf_name': 'PCF_NAME', 'flavor': 'quasiparticle', 'particles': [{'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': [], 'aws_resource': {'ImageId': '$lookup$RESOURCE$Arch', 'KeyName': {'Ref': 'KeyName'}}}, {'pcf_name': 'PCF_NAME', 'flavor': 'FLAVOR', 'parents': [], 'aws_resource': {'KeyName': {'Ref': 'KeyName'}}}]}
}


tests = [
    (test_cft,results["all"],"all"),
    (test_cft,results["Properties"],"Properties"),
    (test_cft,results["DependsOn"],"DependsOn"),
    (test_cft,results["Ref"],["Properties","Ref"]),
    (test_cft,results["FindInMap"],["Properties","FindInMap"]),
]


@pytest.mark.parametrize("definition,result,test_class", tests,ids=list(results.keys()))
def test_apply(definition, result, test_class):
    deepcopy_definition = deepcopy(definition)
    converted_cft = ConvertCFT(deepcopy_definition)
    converted_cft.convert(conversions=test_class)
    assert result == converted_cft.quasiparticle
