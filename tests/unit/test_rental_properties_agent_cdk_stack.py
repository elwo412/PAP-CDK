import aws_cdk as core
import aws_cdk.assertions as assertions

from rental_properties_agent_cdk.rental_properties_agent_cdk_stack import RentalPropertiesAgentCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in rental_properties_agent_cdk/rental_properties_agent_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = RentalPropertiesAgentCdkStack(app, "rental-properties-agent-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
