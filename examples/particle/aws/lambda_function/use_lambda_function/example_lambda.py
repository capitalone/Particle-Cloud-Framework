from pcf.core import State
from pcf.particle.aws.lambda_function.lambda_function import LambdaFunction

# Edit example json to work in your account

# example lambda with function in local zip file
lambda_function_example_zip_json = {
    "pcf_name": "lambda_test", # Required
    "flavor": "lambda_function", # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/lambda.html#Lambda.Client.create_function for a full list of parameters
        "FunctionName": "PCFTest", # Required
        "Runtime": "python3.6", # Required
        "Timeout":30,
        "Role": "arn:aws:iam::account-id:role/lambda-role", # Required
        "Handler": "function_trigger.trigger_handler", # Required
        "Code":{"ZipFile": "lambda_function.zip"} # Required
    }
}

# example lambda with function in a zip file in s3
lambda_function_example_s3_json = {
    "pcf_name": "lambda_test", # Required
    "flavor": "lambda", # Required
    "aws_resource": {
        # Refer to https://boto3.readthedocs.io/en/latest/reference/services/lambda.html#Lambda.Client.create_function for a full list of parameters
        "FunctionName": "PCFTest", # Required
        "Runtime": "python3.6", # Required
        "Timeout": 50,
        "Role": "arn:aws:iam::account-id:role/lambda-role", # Required
        "Handler": "function_trigger.trigger_handler", # Required
        "Code": {"S3Bucket": "pcf-lambda","S3Key": "lambda_function.zip"},
        "Environment": {"Variables":{"test": "letsgo"}}
    }
}

# create lambda particle using local zip file or s3
lambda_function_particle = LambdaFunction(lambda_function_example_zip_json)
# lambda_function_particle = LambdaFunction(lambda_function_example_s3_json)


# example start
lambda_function_particle.set_desired_state(State.running)
lambda_function_particle.apply()

print(lambda_function_particle.get_state())

# example update
updated_def = lambda_function_example_zip_json
updated_def["aws_resource"]["Timeout"] = 40
lambda_function_particle = LambdaFunction(updated_def)
lambda_function_particle.set_desired_state(State.running)
lambda_function_particle.apply()

print(lambda_function_particle.get_state())
print(lambda_function_particle.get_current_state_definition())

# example terminate
lambda_function_particle.set_desired_state(State.terminated)
lambda_function_particle.apply()

print(lambda_function_particle.get_state())
