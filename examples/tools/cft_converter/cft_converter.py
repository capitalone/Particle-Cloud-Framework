from pcf.tools.cft_converter.cft_converter import ConvertCFT

test_cft = {
    "Ec2Instance": {
        "Type": "AWS::EC2::Instance",
        "Properties": {
            "ImageId": {"Fn::FindInMap": "Arch"},
            "KeyName": {"Ref": "KeyName"},
        }
    },
    "Ec2Instance2": {
        "Type": "AWS::EC2::Instance",
        "DependsOn": "Ec2Instance",
        "Properties": {
            "KeyName": {"Ref": "KeyName"},
        }
    }
}

cft = ConvertCFT(test_cft)
cft.convert()
print(cft.cft)
print(cft.quasiparticle)

cft.export_json()
