# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests


class ActionRobotAction(Action):

    def name(self) -> Text:
        return "do_robot_action"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        action_text = str(tracker.latest_message["text"]).lower()
        dispatcher.utter_message(text=action_text)
        if "mir100_1" in action_text:
            url = 'http://127.0.0.1:8001/query'
            params = {'query': action_text}
            requests.get(url, params=params)
            dispatcher.utter_message(text="Acting on Mir100_1")
        elif "mir100_2" in action_text:
            dispatcher.utter_message(text="Acting on Mir100_2")
        elif "mir100_3" in action_text:
            dispatcher.utter_message(text="Acting on Mir100_3")
        elif "conveyorbelt1_dispenser" in action_text:
            url = 'http://127.0.0.1:8010/query'
            params = {'query': action_text}
            requests.get(url, params=params)
            dispatcher.utter_message(text="Acting on ConveyorBelt1_dispenser")
        elif "conveyorbelt2_dispenser" in action_text:
            dispatcher.utter_message(text="Acting on ConveyorBelt2_dispenser")
        elif "conveyorbelt3_dispenser" in action_text:
            dispatcher.utter_message(text="Acting on ConveyorBelt3_dispenser")
        else:
            dispatcher.utter_message(text="unknown robot to act on")

        return []
