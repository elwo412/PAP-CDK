# RPA CDK Python project

## Useful commands

- `cdk ls`: list all stacks in the app
- `cdk synth`: emits the synthesized CloudFormation template
- `cdk deploy`: deploy this stack to your default AWS account/region
- `cdk diff`: compare deployed stack with current state
- `cdk docs`: open CDK documentation

## Updating authorized_keys on EC2

Follow this guide to update `authorized_keys` file in EC2 instance whenever a change to the VPC Stack is made:

1. Navigate to the EC2 instance in AWS management console
2. Click on the instance, and select "Connect using SSM manager"
3. Run the following commands to update the `authorized_keys` file:

```bash
sudo mkdir -p /home/ec2-user/.ssh
sudo touch /home/ec2-user/.ssh/authorized_keys
sudo nano /home/ec2-user/.ssh/authorized_keys 
# Copy in the public key
sudo chmod 700 /home/ec2-user/.ssh
sudo chmod 600 /home/ec2-user/.ssh/authorized_keys
sudo service sshd restart
```

## Database Restoration

### Restoring a database from a dump file

Dumping the local database:

``` powershell
cd "C:\Program Files\PostgreSQL\16\bin"
.\pg_dump.exe -h localhost -U postgres -d RPA > "C:\Users\Elliott\source\repos\RentalPropertiesAgentBackups\<dump-file>.sql"
```

Copying the dump file to an EC2 instance:

```bash
ssh -i <path-to-private-key> ec2-user@<ec2-public-ip>
mkdir ~/rds_dump/
scp -i <path-to-private-key> <path-to-dump-file> ec2-user@<ec2-public-ip>:~/rds_dump/
```

Then restore the database using the following command:

```bash
psql -h <rds-endpoint> -U <username> -d <database-name> -p 5432
CREATE DATABASE <database-name>; # db-name = RPA
# Exit the psql shell

# Check the encoding type of the dump file
file -i <dump-file>.sql
# If the encoding type is not UTF-8, convert the file to UTF-8
iconv -f UTF-16LE -t UTF-8 <dump-file>.sql > <dump-file>utf8.sql # this may take a few minutes
# verify the encoding type again
file -i <dump-file>utf8.sql
# Now restore the database
psql -h [RDS-endpoint] -U [username] -d RPA -p 5432 < <dump-file>utf8.sql
```


### Diagnostic procedures
If the RDS instance is not accessible, check the following:
1. Ensure you have updated the endpoint in pgAdmin in the connection settings
2. Verify EC2 instance reachability by SSHing into the instance
    - `ssh -i <path-to-private-key> ec2-user@<ec2-public-ip>`
3. Test the connection using the `psql` command line tool in the EC2 instance
    - If the ec2 instance is newly created, you may need to install the `psql` tool:

       ```bash
        # If the instance is newly created, install the psql tool
        sudo amazon-linux-extras enable postgresql13
        sudo yum clean metadata
        sudo yum install postgresql

        psql -h <rds-endpoint> -U <username> -d <database-name> -p 5432

        # Note: database-name = dev, username = postgreAdmin
        ```
