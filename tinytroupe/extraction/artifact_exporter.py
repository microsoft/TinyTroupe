import os
import json
import pandas as pd
import pypandoc
import markdown 
from typing import Union, List

from tinytroupe.extraction import logger
from tinytroupe.utils import JsonSerializableRegistry

import tinytroupe.utils as utils

class ArtifactExporter(JsonSerializableRegistry):
    """
    An artifact exporter is responsible for exporting artifacts from TinyTroupe elements, for example 
    in order to create synthetic data files from simulations. 
    """

    def __init__(self, base_output_folder:str) -> None:
        self.base_output_folder = base_output_folder

    def export(self, artifact_name:str, artifact_data:Union[dict, str], content_type:str, content_format:str=None, target_format:str="txt", verbose:bool=False):
        """
        Exports the specified artifact data to a file.

        Args:
            artifact_name (str): The name of the artifact.
            artifact_data (Union[dict, str]): The data to export. If a dict is given, it will be saved as JSON. 
                If a string is given, it will be saved as is.
            content_type (str): The type of the content within the artifact.
            content_format (str, optional): The format of the content within the artifact (e.g., md, csv, etc). Defaults to None.
            target_format (str): The format to export the artifact to (e.g., json, txt, docx, etc).
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        """
        
        # dedent inputs, just in case
        if isinstance(artifact_data, str):
            artifact_data = utils.dedent(artifact_data)
        elif isinstance(artifact_data, dict):
            artifact_data['content'] = utils.dedent(artifact_data['content'])
        else:
            raise ValueError("The artifact data must be either a string or a dictionary.")
        
        # clean the artifact name of invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\t', '\r', ';']
        for char in invalid_chars:
            # check if the character is in the artifact name
            if char in artifact_name:
                # replace the character with an underscore
                artifact_name = artifact_name.replace(char, "-")
                logger.warning(f"Replaced invalid character {char} with hyphen in artifact name '{artifact_name}'.")
        
        artifact_file_path = self._compose_filepath(artifact_data, artifact_name, content_type, target_format, verbose)


        if target_format == "json":
            self._export_as_json(artifact_file_path, artifact_data, content_type, verbose)
        elif target_format == "txt" or target_format == "text" or target_format == "md" or target_format == "markdown":
            self._export_as_txt(artifact_file_path, artifact_data, content_type, verbose)
        elif target_format == "docx":
            self._export_as_docx(artifact_file_path, artifact_data, content_format, verbose)
        else:
            raise ValueError(f"Unsupported target format: {target_format}.")


    def _export_as_txt(self, artifact_file_path:str, artifact_data:Union[dict, str], content_type:str, verbose:bool=False):
        """
        Exports the specified artifact data to a text file.
        """

        with open(artifact_file_path, 'w', encoding="utf-8", errors="replace") as f:
            if isinstance(artifact_data, dict):
                content = artifact_data['content']
            else:
                content = artifact_data
        
            f.write(content)
    
    def _export_as_json(self, artifact_file_path:str, artifact_data:Union[dict, str], content_type:str, verbose:bool=False):
        """
        Exports the specified artifact data to a JSON file.
        """

        with open(artifact_file_path, 'w', encoding="utf-8", errors="replace") as f:
            if isinstance(artifact_data, dict):
                json.dump(artifact_data, f, indent=4)                
            else:
                raise ValueError("The artifact data must be a dictionary to export to JSON.")
    
    def _export_as_docx(self, artifact_file_path:str, artifact_data:Union[dict, str], content_original_format:str, verbose:bool=False):
        """
        Exports the specified artifact data to a DOCX file.
        """

        # original format must be 'text' or 'markdown'
        if content_original_format not in ['text', 'txt', 'markdown', 'md']:
            raise ValueError(f"The original format cannot be {content_original_format} to export to DOCX.")
        else:
            # normalize content value
            content_original_format = 'markdown' if content_original_format == 'md' else content_original_format

        # first, get the content to export. If `artifact_date` is a dict, the contant should be under the key `content`.
        # If it is a string, the content is the string itself.
        # using pypandoc
        if isinstance(artifact_data, dict):
            content = artifact_data['content']
        else:
            content = artifact_data
        
        # first, convert to HTML. This is necessary because pypandoc does not support a GOOD direct conversion from markdown to DOCX.
        html_content = markdown.markdown(content)

        ## write this intermediary HTML to file
        #html_file_path = artifact_file_path.replace(".docx", ".html")
        #with open(html_file_path, 'w', encoding="utf-8", errors="replace") as f:
        #    f.write(html_content)

        # then, convert to DOCX
        pypandoc.convert_text(html_content, 'docx', format='html', outputfile=artifact_file_path)   
    
    ###########################################################
    # IO
    ###########################################################
                  
    def _compose_filepath(self, artifact_data:Union[dict, str], artifact_name:str, content_type:str, target_format:str=None, verbose:bool=False):
        """
        Composes the file path for the artifact to export.

        Args:
            artifact_data (Union[dict, str]): The data to export.
            artifact_name (str): The name of the artifact.
            content_type (str): The type of the content within the artifact.
            content_format (str, optional): The format of the content within the artifact (e.g., md, csv, etc). Defaults to None.
            verbose (bool, optional): Whether to print debug messages. Defaults to False.
        """        

        # Extension definition: 
        #
        # - If the content format is specified, we use it as the part of the extension.
        # - If artificat_data is a dict, we add .json to the extension. Note that if content format was specified, we'd get <content_format>.json.
        # - If artifact_data is a string and no content format is specified, we add .txt to the extension.
        extension = None
        if target_format is not None:
            extension = f"{target_format}"
        elif isinstance(artifact_data, str) and target_format is None:
            extension = "txt"
        
        # content type definition
        if content_type is None:
            subfolder = ""
        else:
            subfolder = content_type

        # save to the specified file name or path, considering the base output folder.
        artifact_file_path = os.path.join(self.base_output_folder, subfolder, f"{artifact_name}.{extension}")    

        # create intermediate directories if necessary
        os.makedirs(os.path.dirname(artifact_file_path), exist_ok=True)

        return artifact_file_path