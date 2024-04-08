from dotenv import load_dotenv
import os

def load_environmental_vars():
    # Determine the environment (e.g., 'development', 'production')
    env = os.getenv('ENVIRONMENT') or 'development'

    # Load the corresponding .env file
    env_file = f"env.\\.env.{env}"
    load_dotenv(dotenv_path=env_file)

    print(f"Environment set to {env}, loaded configuration from {env_file}")