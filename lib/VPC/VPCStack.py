from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_codebuild as codebuild,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_logs,
    SecretValue,
    aws_secretsmanager as secretsmanager,
    RemovalPolicy,
    Duration
)
from constructs import Construct
import boto3, json

class VPCStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Define the VPC
        vpc = ec2.Vpc(
            self, "MyVPC",
            cidr="10.0.0.0/16",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="PublicSubnet", subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(name="PrivateSubnet", subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT)
            ],
            nat_gateways=1
        )

        # Define the Bastion Host Security Group
        bastion_sg = ec2.SecurityGroup(
            self, "BastionSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True
        )
        bastion_sg.add_ingress_rule(
            ec2.Peer.ipv4("68.162.149.11/32"),
            ec2.Port.tcp(22),
            "Allow SSH access from the specified IP address"
        )

        # Define the RDS Security Group
        rds_sg = ec2.SecurityGroup(
            self, "RDSSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True
        )
        rds_sg.add_ingress_rule(
            bastion_sg,
            ec2.Port.tcp(5432),
            "Allow PostgreSQL access from the bastion host"
        )

        # Define the Bastion Host
        bastion_host = ec2.BastionHostLinux(
            self, "BastionHost",
            vpc=vpc,
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=bastion_sg,
            instance_type=ec2.InstanceType("t3.micro"),
        ) # need to add key pair manaully by first using ssm to access, and then create public key to the ec2-user authorized_keys file and restart sshd

        # Retrieve the RDS password from Secrets Manager
        password_secret_value = secretsmanager.Secret.from_secret_complete_arn(
            self, "DBSecret",
            "arn:aws:secretsmanager:us-east-1:260374441616:secret:dbdev/psql/credentials-LT8Z1W"
        ).secret_value_from_json("password")

        # Create the credentials
        secret_creds_db = rds.Credentials.from_username("postgreAdmin", password=password_secret_value)

        # Define the RDS instance
        instance = rds.DatabaseInstance(
            self, "MyRDSInstance",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15_4
            ),
            vpc=vpc,
            credentials=secret_creds_db,
            database_name="dev",
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT),
            security_groups=[rds_sg]
        )

        # CloudWatch log group for the bastion host
        aws_logs.LogGroup(
            self, "BastionHostLogGroup",
            log_group_name=f"/aws/ec2/bastion/{bastion_host.instance_id}",
            retention=aws_logs.RetentionDays.ONE_MONTH
        )