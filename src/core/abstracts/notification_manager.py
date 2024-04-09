from abc import ABC, abstractmethod
from aws_cdk import (
    aws_events as events,
)

class AbstractNotificationManager(ABC):
    def __init__(self, scope, pipeline_name):
        self.scope = scope
        self.pipeline_name = pipeline_name

    def create_notification_rule(self, event_name, target_actions, additional_info=None) -> events.Rule:
        """
        Create a generic notification rule.

        :param event_name: Name of the event to create the rule for.
        :param target_actions: List of actions (e.g., Lambda functions) to trigger.
        :param additional_info: Optional additional information to configure the rule.
        """
        rule = events.Rule(self.scope, event_name,
                           description=additional_info.get('description', ''),
                           event_pattern=self.create_event_pattern(additional_info['event_pattern']))
        for target_action in target_actions:
            rule.add_target(target_action)
        return rule

    def create_event_pattern(self, event_criteria):
        """
        Create an event pattern for triggering the rule.

        :param event_criteria: Criteria defining when the event is triggered.
        """
        return event_criteria