"""
Tools allow agents to accomplish specialized tasks.
"""
import textwrap
import json
import copy

import logging
logger = logging.getLogger("tinytroupe")

import tinytroupe.utils as utils
from tinytroupe.extraction import ArtifactExporter
from tinytroupe.enrichment import TinyEnricher
from tinytroupe.utils import JsonSerializableRegistry


class TinyTool(JsonSerializableRegistry):

    def __init__(self, name, description, owner=None, real_world_side_effects=False, exporter=None, enricher=None):
        """
        Initialize a new tool.

        Args:
            name (str): The name of the tool.
            description (str): A brief description of the tool.
            owner (str): The agent that owns the tool. If None, the tool can be used by anyone.
            real_world_side_effects (bool): Whether the tool has real-world side effects. That is to say, if it has the potential to change the 
                state of the world outside of the simulation. If it does, it should be used with caution.
            exporter (ArtifactExporter): An exporter that can be used to export the results of the tool's actions. If None, the tool will not be able to export results.
            enricher (Enricher): An enricher that can be used to enrich the results of the tool's actions. If None, the tool will not be able to enrich results.
        
        """
        self.name = name
        self.description = description
        self.owner = owner
        self.real_world_side_effects = real_world_side_effects
        self.exporter = exporter
        self.enricher = enricher

    def _process_action(self, agent, action: dict) -> bool:
        raise NotImplementedError("Subclasses must implement this method.")
    
    def _protect_real_world(self):
        if self.real_world_side_effects:
            logger.warning(f" !!!!!!!!!! Tool {self.name} has REAL-WORLD SIDE EFFECTS. This is NOT just a simulation. Use with caution. !!!!!!!!!!")
        
    def _enforce_ownership(self, agent):
        if self.owner is not None and agent.name != self.owner.name:
            raise ValueError(f"Agent {agent.name} does not own tool {self.name}, which is owned by {self.owner.name}.")
    
    def set_owner(self, owner):
        self.owner = owner

    def actions_definitions_prompt(self) -> str:
        raise NotImplementedError("Subclasses must implement this method.")
    
    def actions_constraints_prompt(self) -> str:
        raise NotImplementedError("Subclasses must implement this method.")

    def process_action(self, agent, action: dict) -> bool:
        self._protect_real_world()
        self._enforce_ownership(agent)
        self._process_action(agent, action)


# TODO under development
class TinyCalendar(TinyTool):

    def __init__(self, owner=None):
        super().__init__("calendar", "A basic calendar tool that allows agents to keep track meetings and appointments.", owner=owner, real_world_side_effects=False)
        
        # maps date to list of events. Each event itself is a dictionary with keys "title", "description", "owner", "mandatory_attendees", "optional_attendees", "start_time", "end_time"
        self.calenar = {}
    
    def add_event(self, date, title, description=None, owner=None, mandatory_attendees=None, optional_attendees=None, start_time=None, end_time=None):
        if date not in self.calendar:
            self.calendar[date] = []
        self.calendar[date].append({"title": title, "description": description, "owner": owner, "mandatory_attendees": mandatory_attendees, "optional_attendees": optional_attendees, "start_time": start_time, "end_time": end_time})
    
    def find_events(self, year, month, day, hour=None, minute=None):
        # TODO
        pass

    def _process_action(self, agent, action) -> bool:
        if action['type'] == "CREATE_EVENT" and action['content'] is not None:
            # parse content json
            event_content = json.loads(action['content'])
            
            # checks whether there are any kwargs that are not valid
            valid_keys = ["title", "description", "mandatory_attendees", "optional_attendees", "start_time", "end_time"]
            utils.check_valid_fields(event_content, valid_keys)

            # uses the kwargs to create a new event
            self.add_event(event_content)

            return True

        else:
            return False

    def actions_definitions_prompt(self) -> str:
        prompt = \
            """
              - CREATE_EVENT: You can create a new event in your calendar. The content of the event has many fields, and you should use a JSON format to specify them. Here are the possible fields:
                * title: The title of the event. Mandatory.
                * description: A brief description of the event. Optional.
                * mandatory_attendees: A list of agent names who must attend the event. Optional.
                * optional_attendees: A list of agent names who are invited to the event, but are not required to attend. Optional.
                * start_time: The start time of the event. Optional.
                * end_time: The end time of the event. Optional.
            """
        # TODO how the atendee list will be handled? How will they be notified of the invitation? I guess they must also have a calendar themselves. <-------------------------------------

        return utils.dedent(prompt)
        
    
    def actions_constraints_prompt(self) -> str:
        prompt = \
            """
              
            """
            # TODO

        return textwrap.dedent(prompt)
    


class TinyWordProcessor(TinyTool):

    def __init__(self, owner=None, exporter=None, enricher=None):
        super().__init__("wordprocessor", "A basic word processor tool that allows agents to write documents.", owner=owner, real_world_side_effects=False, exporter=exporter, enricher=enricher)
        
    def write_document(self, title, content, author=None):
        logger.debug(f"Writing document with title {title} and content: {content}")

        if self.enricher is not None:
            requirements =\
            """
            Turn any draft or outline into an actual and long document, with many, many details. Include tables, lists, and other elements.
            The result **MUST** be at least 5 times larger than the original content in terms of characters - do whatever it takes to make it this long and detailed.
            """
                
            content = self.enricher.enrich_content(requirements=requirements, 
                                                    content=content, 
                                                    content_type="Document", 
                                                    context_info=None,
                                                    context_cache=None, verbose=False)    
            
        if self.exporter is not None:
            self.exporter.export(artifact_name=f"{title}.{author}", artifact_data= content, content_type="Document", content_format="md", target_format="md")
            self.exporter.export(artifact_name=f"{title}.{author}", artifact_data= content, content_type="Document", content_format="md", target_format="docx")

            json_doc = {"title": title, "content": content, "author": author}
            self.exporter.export(artifact_name=f"{title}.{author}", artifact_data= json_doc, content_type="Document", content_format="md", target_format="json")

    def _process_action(self, agent, action) -> bool:
        try:
            if action['type'] == "WRITE_DOCUMENT" and action['content'] is not None:
                # parse content json
                if isinstance(action['content'], str):
                    doc_spec = json.loads(action['content'])  
                else:
                    doc_spec = action['content']
                
                # checks whether there are any kwargs that are not valid
                valid_keys = ["title", "content", "author"]
                utils.check_valid_fields(doc_spec, valid_keys)

                # uses the kwargs to create a new document
                self.write_document(**doc_spec)

                return True

            else:
                return False
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON content: {e}. Original content: {action['content']}")
            return False

    def actions_definitions_prompt(self) -> str:
        prompt = \
            """
            - WRITE_DOCUMENT: you can create a new document. The content of the document has many fields, and you should use a JSON format to specify them. Here are the possible fields:
                * title: The title of the document. Mandatory.
                * content: The actual content of the document. You **must** use Markdown to format this content. Mandatory.
                * author: The author of the document. You should put your own name. Optional.
            """
        return utils.dedent(prompt)
        
    
    def actions_constraints_prompt(self) -> str:
        prompt = \
            """
            - Whenever you WRITE_DOCUMENT, you write all the content at once. Moreover, the content should be long and detailed, unless there's a good reason for it not to be.
            - When you WRITE_DOCUMENT, you follow these additional guidelines:
                * For any milestones or timelines mentioned, try mentioning specific owners or partner teams, unless there's a good reason not to do so.
            """
        return utils.dedent(prompt)