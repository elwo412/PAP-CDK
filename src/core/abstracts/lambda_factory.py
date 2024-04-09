from abc import ABC, abstractmethod
from aws_cdk import (
    aws_lambda as lambda_,
    Duration
)
from constructs import Construct
import os, shutil, sys, hashlib

class AbstractLambdaFactory(ABC):
    def __init__(self, scope: Construct):
        self.scope = scope

    def create_lambda(self, id: str, handler: str, runtime: lambda_.Runtime, code: lambda_.Code, environment: dict = {}, timeout: Duration = Duration.seconds(5)) -> lambda_.Function:
        return lambda_.Function(
            self.scope, id,
            function_name=id,
            handler=handler,
            runtime=runtime,
            code=code,
            environment=environment,
            timeout=timeout,
        )
        
    def create_package_directory(self, source_dir):
        # Check if the source directory exists
        if not os.path.exists(source_dir):
            raise Exception(f"Source directory {source_dir} does not exist.")
        
        package_dir = os.path.join(source_dir, "package")
        requirements_path = os.path.join(source_dir, "requirements.txt")
        hash_file_path = os.path.join(package_dir, "requirements.hash")

        # Compute the current hash of requirements.txt
        with open(requirements_path, "rb") as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()

        # Check if the package directory needs to be updated
        if os.path.exists(hash_file_path):
            with open(hash_file_path, "r") as f:
                stored_hash = f.read().strip()
            
            if current_hash == stored_hash:
                print("Packages are up-to-date.")
                return package_dir

        # If reaching here, packages need to be updated
        print("Updating packages...")

        if os.path.exists(package_dir):
            # Remove the package directory and all its contents
            shutil.rmtree(package_dir)

        # Create the package directory
        os.makedirs(package_dir)

        # pip install the required packages
        pip_command = "pip3" if sys.platform in ["linux", "darwin"] else "pip"
        os.system(f"{pip_command} install -r {requirements_path} -t {package_dir}")

        # Save the current hash to the package directory
        with open(hash_file_path, "w") as f:
            f.write(current_hash)

        # Copy the source files into the package directory
        for filename in os.listdir(source_dir):
            if filename.endswith(".py"):
                shutil.copy(os.path.join(source_dir, filename), package_dir)

        return package_dir