from aws_cdk import aws_ec2 as ec2
from constructs import Construct
from cdk_fck_nat import FckNatInstanceProvider

class NatProvider(Construct):
    def __init__(self, scope: Construct, id: str, instance_type: str):
        super().__init__(scope, id)

        # Define the FckNatInstanceProvider
        self._nat_instance_provider = FckNatInstanceProvider(
            instance_type=ec2.InstanceType(instance_type)
        )

    @property
    def instance(self):
        return self._nat_instance_provider
    
    def add_ingress_rule(self, peer: ec2.Peer, port: ec2.Port, description: str):
        self._nat_instance_provider.connections.security_groups[0].add_ingress_rule(peer, port, description)