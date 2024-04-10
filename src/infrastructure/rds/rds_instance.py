from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import RemovalPolicy
from constructs import Construct

class RdsInstance(Construct):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, bastion_sg: ec2.SecurityGroup, vpc_subnet: ec2.SubnetSelection):
        super().__init__(scope, id)
        
        self.vpc = vpc
        self.vpc_subnet = vpc_subnet

        # Define the RDS Security Group
        self.rds_sg = ec2.SecurityGroup(
            self, "RDSSecurityGroup",
            vpc=self.vpc,
            allow_all_outbound=True
        )
        self.rds_sg.add_ingress_rule(
            bastion_sg,
            ec2.Port.tcp(5432),
            "Allow PostgreSQL access from the bastion host"
        )

        # Retrieve the RDS password from Secrets Manager
        password_secret_value = secretsmanager.Secret.from_secret_complete_arn(
            self, "DBSecret",
            "arn:aws:secretsmanager:us-east-1:260374441616:secret:dbdev/psql/credentials-LT8Z1W"
        ).secret_value_from_json("password")

        # Create the credentials
        #secret_creds_db = rds.Credentials.from_username("postgreAdmin", password=password_secret_value)
        self.secret_creds_db = rds.Credentials.from_generated_secret("postgreAdmin", secret_name="dbdev/psql/credentials-LT8Z1W")
        
    def set_rds_sg_ingress_rule(self, peer: ec2.SecurityGroup, port: ec2.Port, description: str):
        self.rds_sg.add_ingress_rule(peer, port, description)
        
    def create(self):
                # Define the RDS instance
        self.instance = rds.DatabaseInstance(
            self, "MyRDSInstance",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15_4
            ),
            vpc=self.vpc,
            credentials=self.secret_creds_db,
            database_name="dev",
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc_subnets=self.vpc_subnet,
            security_groups=[self.rds_sg],
            removal_policy=RemovalPolicy.RETAIN
        )