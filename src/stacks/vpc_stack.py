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
from cdk_fck_nat import FckNatInstanceProvider
from src.infrastructure.vpc.nat_provider import NatProvider
from src.infrastructure.vpc.bastion_host import BastionHost
from src.infrastructure.rds.rds_instance import RdsInstance

class VPCStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        nat_provider = NatProvider(self, id="Nat Provider", instance_type="t4g.micro")

        # Define the VPC
        vpc = ec2.Vpc(
            self, "MyVPC",
            cidr="10.0.0.0/16",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="PublicSubnet", subnet_type=ec2.SubnetType.PUBLIC),
                ec2.SubnetConfiguration(name="PrivateSubnet", subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT)
            ],
            nat_gateway_provider=nat_provider.instance
        )
        
        # Add ingress rule to NAT instance's security group
        nat_provider.add_ingress_rule(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.all_traffic(),
            "Allow all traffic from within the VPC"
        )
        
        
        bastion_host = BastionHost(self, "BastionHost", vpc=vpc)
        rds_instance = RdsInstance(self, "RdsInstance", vpc=vpc, bastion_sg=bastion_host.security_group)