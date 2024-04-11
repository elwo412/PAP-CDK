from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_iam as iam
from aws_cdk import Duration
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct

class LambdaInstance(Construct):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, vpc_subnet: ec2.SubnetSelection):
        super().__init__(scope, id)
        self.vpc = vpc
        self.vpc_subnet = vpc_subnet
        
        self.execution_role = iam.Role(self, "LambdaExecutionRole",
                            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                            managed_policies=[
                                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
                            ])
        
        # Security group for the Lambda function
        self.lambda_sg = ec2.SecurityGroup(
            self, "LambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for Lambda function in private subnet"
        )
        
    @property
    def lambda_function(self) -> lambda_.Function:
        return self._lambda_function
    
    def set_egress_rule(self, peer: ec2.SecurityGroup, connection: ec2.Port, description: str):
        self.lambda_sg.add_egress_rule(peer, connection, description)
        
    def create(self):
        # Get the rds credentials from Secrets Manager at secret name of dbdev/postgre/credentials
        # this will have username, host, and password
        full_secret_arn = "arn:aws:secretsmanager:us-east-1:260374441616:secret:dbdev/postgre/credentials-wjpT0A"
        secret_access_policy_statement = iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=[full_secret_arn],
            effect=iam.Effect.ALLOW
        )
        self.execution_role.add_to_policy(secret_access_policy_statement)
        
        # Create the lambda function
        self._lambda_function = lambda_.Function(
            self, f"FastApiLambda-DEV",
            role=self.execution_role,
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="app.handler",
            code=lambda_.InlineCode("def handler(event, context): return {'statusCode': 200, 'body': 'hello world'}"), # placeholder code
            vpc=self.vpc,
            vpc_subnets=self.vpc_subnet,
            security_groups=[ec2.SecurityGroup(
                self, "LambdaSecurityGroupPrivate",
                vpc=self.vpc,
                allow_all_outbound=True,
                description="Security group for Lambda function in private subnet"
            ), self.lambda_sg],
            environment={
                # environment variables
                "DB_CREDENTIALS_SECRET_ARN": full_secret_arn,
                "ENV": "dev",
                "POSTGRES_DB" : "rpa"
            },
            timeout=Duration.seconds(10)
        )