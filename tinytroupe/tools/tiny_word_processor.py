
from tinytroupe.tools import logger, TinyTool


import tinytroupe.utils as utils

class TinyWordProcessor(TinyTool):
    """
    A per-agent word processor tool that lets an agent write documents.

    This tool holds no cross-agent state, so it needs no shared service: each agent simply owns
    its own instance (its own "app"). Produced documents can optionally be enriched and exported
    via the supplied ``enricher`` / ``exporter`` collaborators.
    """

    action_namespace = "TINYWORDPROCESSOR"

    def __init__(self, owner=None, exporter=None, enricher=None, id=None, name=None):
        super().__init__(
            id=id,
            name=name if name is not None else "wordprocessor",
            description="A basic word processor tool that allows agents to write documents.",
            owner=owner,
            real_world_side_effects=False,
            exporter=exporter,
            enricher=enricher,
        )
        
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
            if author is not None:
                artifact_name = f"{title}.{author}"
            else:
                artifact_name = title
            self.exporter.export(artifact_name=artifact_name, artifact_data= content, content_type="Document", content_format="md", target_format="md")
            self.exporter.export(artifact_name=artifact_name, artifact_data= content, content_type="Document", content_format="md", target_format="docx")

            json_doc = {"title": title, "content": content, "author": author}
            self.exporter.export(artifact_name=artifact_name, artifact_data= json_doc, content_type="Document", content_format="md", target_format="json")

    def _process_action(self, agent, action) -> bool:
        from tinytroupe.tools.tiny_tool import parse_action_namespace

        _namespace, verb = parse_action_namespace(action.get("type"))
        if verb == "WRITE_DOCUMENT" and action['content'] is not None:
            # content may be a JSON string or an already-parsed dict
            if isinstance(action['content'], str):
                doc_spec = utils.extract_json(action['content'])
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

    def actions_definitions_prompt(self) -> str:
        prompt = \
            """
            - TINYWORDPROCESSOR::WRITE_DOCUMENT: you can create a new document. The content of the document has many fields, and you **must** use a JSON format to specify them. Here are the possible fields:
                * title: The title of the document. Mandatory.
                * content: The actual content of the document. You **must** use Markdown to format this content. Mandatory.
                * author: The author of the document. You should put your own name. Optional.
            """
        return utils.dedent(prompt)
        
    
    def actions_constraints_prompt(self) -> str:
        prompt = \
            """
            - Whenever you TINYWORDPROCESSOR::WRITE_DOCUMENT, you write all the content at once. Moreover, the content should be long and detailed, unless there's a good reason for it not to be.
            - Whenever you TINYWORDPROCESSOR::WRITE_DOCUMENT, you **must** embed the content in a JSON object. Use only valid escape sequences in the JSON content.
            - When you TINYWORDPROCESSOR::WRITE_DOCUMENT, you follow these additional guidelines:
                * For any milestones or timelines mentioned, try mentioning specific owners or partner teams, unless there's a good reason not to do so.
            """
        return utils.dedent(prompt)