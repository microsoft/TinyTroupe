import json
import re

from tinytroupe.tools import logger, TinyTool


import tinytroupe.utils as utils


def _extract_document_spec_fallback(raw: str) -> dict | None:
    """
    Fallback when extract_json fails on WRITE_DOCUMENT content (common with
    truncated or poorly escaped LLM output). Tries repair + regex extraction.
    """
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    # Try repairing truncated JSON (model often cuts off mid-string)
    for suffix in ['"', '"}', '"}]', '" }', '" }']:
        repaired = raw + suffix
        parsed = utils.extract_json(repaired)
        if parsed and isinstance(parsed, dict) and parsed.get("title"):
            return parsed
    # Regex fallback: extract title and content
    title_m = re.search(r'"title"\s*:\s*"([^"]*)"', raw)
    if not title_m:
        return None
    title = title_m.group(1)
    content_m = re.search(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', raw, re.DOTALL)
    if content_m:
        content = content_m.group(1)
    else:
        # Truncated JSON: content may lack closing quote; take from "content": " to end
        prefix = re.search(r'"content"\s*:\s*"', raw)
        content = raw[prefix.end() :] if prefix else ""
    # Unescape common JSON escapes (do \\ first to avoid double-converting)
    if content:
        content = (
            content.replace("\\\\", "\x00")  # temp placeholder
            .replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace('\\"', '"')
            .replace("\x00", "\\")
        )
    return {"title": title, "content": content or "(content could not be extracted)", "author": None}


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
            if author is not None:
                artifact_name = f"{title}.{author}"
            else:
                artifact_name = title
            self.exporter.export(artifact_name=artifact_name, artifact_data= content, content_type="Document", content_format="md", target_format="md")
            self.exporter.export(artifact_name=artifact_name, artifact_data= content, content_type="Document", content_format="md", target_format="docx")

            json_doc = {"title": title, "content": content, "author": author}
            self.exporter.export(artifact_name=artifact_name, artifact_data= json_doc, content_type="Document", content_format="md", target_format="json")

    def _process_action(self, agent, action) -> bool:
        try:
            if action['type'] == "WRITE_DOCUMENT" and action['content'] is not None:
                # parse content json
                if isinstance(action['content'], str):
                    doc_spec = utils.extract_json(action['content'])
                    if doc_spec is None:
                        doc_spec = _extract_document_spec_fallback(action['content'])
                else:
                    doc_spec = action['content']

                if doc_spec is None:
                    logger.error("Could not parse WRITE_DOCUMENT content as JSON")
                    return False

                # Use agent name when author is missing (fallback parsing often omits it)
                if doc_spec.get("author") is None and agent is not None:
                    doc_spec = {**doc_spec, "author": agent.name}
                # Ensure content exists (model sometimes returns only title)
                if doc_spec.get("content") is None or doc_spec.get("content") == "":
                    doc_spec = {**doc_spec, "content": f"# {doc_spec.get('title', 'Document')}\n\n(Content not provided)"}

                # checks whether there are any kwargs that are not valid
                valid_keys = ["title", "content", "author"]
                utils.check_valid_fields(doc_spec, valid_keys)

                # uses the kwargs to create a new document
                self.write_document(**doc_spec)

                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Error processing action: {e}")
            return False

    def actions_definitions_prompt(self) -> str:
        prompt = \
            """
            - WRITE_DOCUMENT: you can create a new document. The content of the document has many fields, and you **must** use a JSON format to specify them. Here are the possible fields:
                * title: The title of the document. Mandatory.
                * content: The actual content of the document. You **must** use Markdown to format this content. Mandatory.
                * author: The author of the document. You should put your own name. Optional.
            """
        return utils.dedent(prompt)
        
    
    def actions_constraints_prompt(self) -> str:
        prompt = \
            """
            - Whenever you WRITE_DOCUMENT, you write all the content at once. Moreover, the content should be long and detailed, unless there's a good reason for it not to be.
            - Whenever you WRITE_DOCUMENT, you **must** embed the content in a JSON object. Use only valid escape sequences in the JSON content.
            - When you WRITE_DOCUMENT, you follow these additional guidelines:
                * For any milestones or timelines mentioned, try mentioning specific owners or partner teams, unless there's a good reason not to do so.
            """
        return utils.dedent(prompt)