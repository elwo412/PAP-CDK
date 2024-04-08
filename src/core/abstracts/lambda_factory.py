from abc import ABC, abstractmethod
from aws_cdk import (
    aws_lambda as lambda_,
    Duration
)
from constructs import Construct
import os, shutil, sys

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
        package_dir = source_dir+"/package"
        if os.path.exists(package_dir):
            # Remove the package directory and all its contents
            shutil.rmtree(package_dir)

        # Create the package directory
        os.makedirs(package_dir)

        # pip install the required packages
        pip_command = "pip3" if sys.platform == "linux" or sys.platform == "darwin" else "pip"
        os.system(f"{pip_command} install -r {source_dir}/requirements.txt -t {package_dir}")

        # Copy the source files into the package directory
        for filename in os.listdir(source_dir):
            if filename.endswith(".py"):
                shutil.copy(os.path.join(source_dir, filename), package_dir)

        return package_dir