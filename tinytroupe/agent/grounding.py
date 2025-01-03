from tinytroupe.utils import JsonSerializableRegistry
import tinytroupe.utils as utils

from tinytroupe.agent import logger
from llama_index.core import  VectorStoreIndex, SimpleDirectoryReader



#######################################################################################################################
# Grounding connectors
#######################################################################################################################

class GroundingConnector(JsonSerializableRegistry):
    """
    An abstract class representing a grounding connector. A grounding connector is a component that allows an agent to ground
    its knowledge in external sources, such as files, web pages, databases, etc.
    """

    serializable_attributes = ["name"]

    def __init__(self, name:str) -> None:
        self.name = name
    
    def retrieve_relevant(self, relevance_target:str, source:str, top_k=20) -> list:
        raise NotImplementedError("Subclasses must implement this method.")
    
    def retrieve_by_name(self, name:str) -> str:
        raise NotImplementedError("Subclasses must implement this method.")
    
    def list_sources(self) -> list:
        raise NotImplementedError("Subclasses must implement this method.")


@utils.post_init
class BaseSemanticGroundingConnector(GroundingConnector):
    """
    A base class for semantic grounding connectors. A semantic grounding connector is a component that indexes and retrieves
    documents based on so-called "semantic search" (i.e, embeddings-based search). This specific implementation
    is based on the VectorStoreIndex class from the LLaMa-Index library. Here, "documents" refer to the llama-index's
    data structure that stores a unit of content, not necessarily a file.
    """

    serializable_attributes = ["documents"]

    def __init__(self, name:str="Semantic Grounding") -> None:
        super().__init__(name)

        self.documents = None 
        self.name_to_document = None

        # @post_init ensures that _post_init is called after the __init__ method
    
    def _post_init(self):
        """
        This will run after __init__, since the class has the @post_init decorator.
        It is convenient to separate some of the initialization processes to make deserialize easier.
        """
        self.index = None

        if not hasattr(self, 'documents') or self.documents is None:
            self.documents = []
        
        if not hasattr(self, 'name_to_document') or self.name_to_document is None:
            self.name_to_document = {}

        self.add_documents(self.documents)       

    def retrieve_relevant(self, relevance_target:str, top_k=20) -> list:
        """
        Retrieves all values from memory that are relevant to a given target.
        """
        if self.index is not None:
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(relevance_target)
        else:
            nodes = []

        retrieved = []
        for node in nodes:
            content = "SOURCE: " + node.metadata.get('file_name', '(unknown)')
            content += "\n" + "SIMILARITY SCORE:" + str(node.score)
            content += "\n" + "RELEVANT CONTENT:" + node.text
            retrieved.append(content)

            logger.debug(f"Content retrieved: {content[:200]}")

        return retrieved
    
    def retrieve_by_name(self, name:str) -> list:
        """
        Retrieves a content source by its name.
        """
        # TODO also optionally provide a relevance target?
        results = []
        if self.name_to_document is not None and name in self.name_to_document:
            docs = self.name_to_document[name]
            for i, doc in enumerate(docs):
                if doc is not None:
                    content = f"SOURCE: {name}\n"
                    content += f"PAGE: {i}\n"
                    content += "CONTENT: \n" + doc.text[:10000] # TODO a more intelligent way to limit the content
                    results.append(content)
                    
        return results
        
        
    def list_sources(self) -> list:
        """
        Lists the names of the available content sources.
        """
        if self.name_to_document is not None:
            return list(self.name_to_document.keys())
        else:
            return []
    
    def add_document(self, document, doc_to_name_func=None) -> None:
        """
        Indexes a document for semantic retrieval.
        """
        self.add_documents([document], doc_to_name_func)

    def add_documents(self, new_documents, doc_to_name_func=None) -> list:
        """
        Indexes documents for semantic retrieval.
        """
        # index documents by name
        if len(new_documents) > 0:
            # add the new documents to the list of documents
            self.documents += new_documents

            # process documents individually too
            for document in new_documents:
                
                # out of an abundance of caution, we sanitize the text
                document.text = utils.sanitize_raw_string(document.text)

                if doc_to_name_func is not None:
                    name = doc_to_name_func(document)
                    
                    # self.name_to_document[name] contains a list, since each source file could be split into multiple pages
                    if name in self.name_to_document:
                        self.name_to_document[name].append(document)
                    else:
                        self.name_to_document[name] = [document]


            # index documents for semantic retrieval
            if self.index is None:
                self.index = VectorStoreIndex.from_documents(self.documents)
            else:
                self.index.refresh(self.documents)
    
    

@utils.post_init
class LocalFilesGroundingConnector(BaseSemanticGroundingConnector):

    serializable_attributes = ["folders_paths"]

    def __init__(self, name:str="Local Files", folders_paths: list=None) -> None:
        super().__init__(name)

        self.folders_paths = folders_paths

        # @post_init ensures that _post_init is called after the __init__ method
    
    def _post_init(self):
        """
        This will run after __init__, since the class has the @post_init decorator.
        It is convenient to separate some of the initialization processes to make deserialize easier.
        """
        self.loaded_folders_paths = []

        if not hasattr(self, 'folders_paths') or self.folders_paths is None:
            self.folders_paths = []

        self.add_folders(self.folders_paths)

    def add_folders(self, folders_paths:list) -> None:
        """
        Adds a path to a folder with files used for grounding.
        """

        if folders_paths is not None:
            for folder_path in folders_paths:
                try:
                    logger.debug(f"Adding the following folder to grounding index: {folder_path}")
                    self.add_folder(folder_path)
                except (FileNotFoundError, ValueError) as e:
                    print(f"Error: {e}")
                    print(f"Current working directory: {os.getcwd()}")
                    print(f"Provided path: {folder_path}")
                    print("Please check if the path exists and is accessible.")

    def add_folder(self, folder_path:str) -> None:
        """
        Adds a path to a folder with files used for grounding.
        """

        if folder_path not in self.loaded_folders_paths:
            self._mark_folder_as_loaded(folder_path)

            # for PDF files, please note that the document will be split into pages: https://github.com/run-llama/llama_index/issues/15903
            new_files = SimpleDirectoryReader(folder_path).load_data()
            self.add_documents(new_files, lambda doc: doc.metadata["file_name"])
    
    def add_file_path(self, file_path:str) -> None:
        """
        Adds a path to a file used for grounding.
        """
        # a trick to make SimpleDirectoryReader work with a single file
        new_files = SimpleDirectoryReader(input_files=[file_path]).load_data()
        
        logger.debug(f"Adding the following file to grounding index: {new_files}")
        self.add_documents(new_files, lambda doc: doc.metadata["file_name"])
    
    def _mark_folder_as_loaded(self, folder_path:str) -> None:
        if folder_path not in self.loaded_folders_paths:
            self.loaded_folders_paths.append(folder_path)
        
        if folder_path not in self.folders_paths:
            self.folders_paths.append(folder_path)
    

@utils.post_init
class WebPagesGroundingConnector(BaseSemanticGroundingConnector):

    serializable_attributes = ["web_urls"]

    def __init__(self, name:str="Web Pages", web_urls: list=None) -> None:
        super().__init__(name)

        self.web_urls = web_urls

        # @post_init ensures that _post_init is called after the __init__ method
    
    def _post_init(self):
        self.loaded_web_urls = []

        if not hasattr(self, 'web_urls') or self.web_urls is None:
            self.web_urls = []

        # load web urls
        self.add_web_urls(self.web_urls)
    
    def add_web_urls(self, web_urls:list) -> None:
        """ 
        Adds the data retrieved from the specified URLs to grounding.
        """
        filtered_web_urls = [url for url in web_urls if url not in self.loaded_web_urls]
        for url in filtered_web_urls:
            self._mark_web_url_as_loaded(url)

        if len(filtered_web_urls) > 0:
            new_documents = SimpleWebPageReader(html_to_text=True).load_data(filtered_web_urls)
            self.add_documents(new_documents, lambda doc: doc.id_)
    
    def add_web_url(self, web_url:str) -> None:
        """
        Adds the data retrieved from the specified URL to grounding.
        """
        # we do it like this because the add_web_urls could run scrapes in parallel, so it is better
        # to implement this one in terms of the other
        self.add_web_urls([web_url])
    
    def _mark_web_url_as_loaded(self, web_url:str) -> None:
        if web_url not in self.loaded_web_urls:
            self.loaded_web_urls.append(web_url)
        
        if web_url not in self.web_urls:
            self.web_urls.append(web_url)
    
