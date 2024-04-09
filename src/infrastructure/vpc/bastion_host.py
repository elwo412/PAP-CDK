
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_logs
from constructs import Construct

class BastionHost(Construct):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, allowed_ssh_ip: str = "68.162.149.11/32"):
        super().__init__(scope, id)

        # Define the Bastion Host Security Group
        bastion_sg = ec2.SecurityGroup(
            self, "BastionSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for the Bastion Host"
        )
        
        # Add ingress rule for SSH access
        bastion_sg.add_ingress_rule(
            ec2.Peer.ipv4(allowed_ssh_ip),
            ec2.Port.tcp(22),
            "Allow SSH access from the specified IP address"
        )

        # Define the Bastion Host
        bastion_host = ec2.BastionHostLinux( # NOTE: need to add key pair manaully by first using ssm to access, and then create public key to the ec2-user authorized_keys file and restart sshd
            self, "BastionHost",
            vpc=vpc,
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=bastion_sg,
            instance_type=ec2.InstanceType("t3.micro"),
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(100)
                )
            ]
        )

        # CloudWatch log group for the Bastion Host
        log_group = aws_logs.LogGroup(
            self, "BastionHostLogGroup",
            log_group_name=f"/aws/ec2/bastion/{bastion_host.instance_id}",
            retention=aws_logs.RetentionDays.ONE_MONTH,
        )

        # Expose bastion host and security group for external reference if needed
        self.bastion_host = bastion_host
        self.security_group = bastion_sg