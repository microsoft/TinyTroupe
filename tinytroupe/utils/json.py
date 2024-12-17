import json
import copy

from tinytroupe.utils import logger

class JsonSerializableRegistry:
    """
    A mixin class that provides JSON serialization, deserialization, and subclass registration.
    """
    
    class_mapping = {}

    def to_json(self, include: list = None, suppress: list = None, file_path: str = None) -> dict:
        """
        Returns a JSON representation of the object.
        
        Args:
            include (list, optional): Attributes to include in the serialization. Will override the default behavior.
            suppress (list, optional): Attributes to suppress from the serialization. Will override the default behavior.
            file_path (str, optional): Path to a file where the JSON will be written.
        """
        # Gather all serializable attributes from the class hierarchy
        serializable_attrs = set()
        suppress_attrs = set()
        for cls in self.__class__.__mro__:  # Traverse the class hierarchy
            if hasattr(cls, 'serializable_attributes') and isinstance(cls.serializable_attributes, list):
                serializable_attrs.update(cls.serializable_attributes)
            if hasattr(cls, 'suppress_attributes_from_serialization') and isinstance(cls.suppress_attributes_from_serialization, list):
                suppress_attrs.update(cls.suppress_attributes_from_serialization)
        
        # Override attributes with method parameters if provided
        if include:
            serializable_attrs = set(include)
        if suppress:
            suppress_attrs.update(suppress)
        
        result = {"json_serializable_class_name": self.__class__.__name__}
        for attr in serializable_attrs if serializable_attrs else self.__dict__:
            if attr not in suppress_attrs:
                value = getattr(self, attr, None)
                if isinstance(value, JsonSerializableRegistry):
                    result[attr] = value.to_json()
                elif isinstance(value, list):
                    result[attr] = [item.to_json() if isinstance(item, JsonSerializableRegistry) else copy.deepcopy(item) for item in value]
                elif isinstance(value, dict):
                    result[attr] = {k: v.to_json() if isinstance(v, JsonSerializableRegistry) else copy.deepcopy(v) for k, v in value.items()}
                else:
                    result[attr] = copy.deepcopy(value)
        
        if file_path:
            # Create directories if they do not exist
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(result, f, indent=4)
        
        return result

    @classmethod
    def from_json(cls, json_dict_or_path, suppress: list = None, post_init_params: dict = None):
        """
        Loads a JSON representation of the object and creates an instance of the class.
        
        Args:
            json_dict_or_path (dict or str): The JSON dictionary representing the object or a file path to load the JSON from.
            suppress (list, optional): Attributes to suppress from being loaded.
            
        Returns:
            An instance of the class populated with the data from json_dict_or_path.
        """
        if isinstance(json_dict_or_path, str):
            with open(json_dict_or_path, 'r') as f:
                json_dict = json.load(f)
        else:
            json_dict = json_dict_or_path
        
        subclass_name = json_dict.get("json_serializable_class_name")
        target_class = cls.class_mapping.get(subclass_name, cls)
        instance = target_class.__new__(target_class)  # Create an instance without calling __init__
        
        # Gather all serializable attributes from the class hierarchy
        serializable_attrs = set()
        custom_serialization_initializers = {}
        suppress_attrs = set(suppress) if suppress else set()
        for cls in target_class.__mro__:
            if hasattr(cls, 'serializable_attributes') and isinstance(cls.serializable_attributes, list):
                serializable_attrs.update(cls.serializable_attributes)
            if hasattr(cls, 'custom_serialization_initializers') and isinstance(cls.custom_serialization_initializers, dict):
                custom_serialization_initializers.update(cls.custom_serialization_initializers)
            if hasattr(cls, 'suppress_attributes_from_serialization') and isinstance(cls.suppress_attributes_from_serialization, list):
                suppress_attrs.update(cls.suppress_attributes_from_serialization)
        
        # Assign values only for serializable attributes if specified, otherwise assign everything
        for key in serializable_attrs if serializable_attrs else json_dict:
            if key in json_dict and key not in suppress_attrs:
                value = json_dict[key]
                if key in custom_serialization_initializers:
                    # Use custom initializer if provided
                    setattr(instance, key, custom_serialization_initializers[key](value))
                elif isinstance(value, dict) and 'json_serializable_class_name' in value:
                    # Assume it's another JsonSerializableRegistry object
                    setattr(instance, key, JsonSerializableRegistry.from_json(value))
                elif isinstance(value, list):
                    # Handle collections, recursively deserialize if items are JsonSerializableRegistry objects
                    deserialized_collection = []
                    for item in value:
                        if isinstance(item, dict) and 'json_serializable_class_name' in item:
                            deserialized_collection.append(JsonSerializableRegistry.from_json(item))
                        else:
                            deserialized_collection.append(copy.deepcopy(item))
                    setattr(instance, key, deserialized_collection)
                else:
                    setattr(instance, key, copy.deepcopy(value))
        
        # Call post-deserialization initialization if available
        if hasattr(instance, '_post_deserialization_init') and callable(instance._post_deserialization_init):
            post_init_params = post_init_params if post_init_params else {}
            instance._post_deserialization_init(**post_init_params)
        
        return instance

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Register the subclass using its name as the key
        JsonSerializableRegistry.class_mapping[cls.__name__] = cls
        
        # Automatically extend serializable attributes and custom initializers from parent classes 
        if hasattr(cls, 'serializable_attributes') and isinstance(cls.serializable_attributes, list):
            for base in cls.__bases__:
                if hasattr(base, 'serializable_attributes') and isinstance(base.serializable_attributes, list):
                    cls.serializable_attributes = list(set(base.serializable_attributes + cls.serializable_attributes))
        
        if hasattr(cls, 'suppress_attributes_from_serialization') and isinstance(cls.suppress_attributes_from_serialization, list):
            for base in cls.__bases__:
                if hasattr(base, 'suppress_attributes_from_serialization') and isinstance(base.suppress_attributes_from_serialization, list):
                    cls.suppress_attributes_from_serialization = list(set(base.suppress_attributes_from_serialization + cls.suppress_attributes_from_serialization))
        
        if hasattr(cls, 'custom_serialization_initializers') and isinstance(cls.custom_serialization_initializers, dict):
            for base in cls.__bases__:
                if hasattr(base, 'custom_serialization_initializers') and isinstance(base.custom_serialization_initializers, dict):
                    base_initializers = base.custom_serialization_initializers.copy()
                    base_initializers.update(cls.custom_serialization_initializers)
                    cls.custom_serialization_initializers = base_initializers

    def _post_deserialization_init(self, **kwargs):
        # if there's a _post_init method, call it after deserialization
        if hasattr(self, '_post_init'):
            self._post_init(**kwargs)


def post_init(cls):
    """
    Decorator to enforce a post-initialization method call in a class, if it has one.
    The method must be named `_post_init`.
    """
    original_init = cls.__init__

    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if hasattr(cls, '_post_init'):
            cls._post_init(self)

    cls.__init__ = new_init
    return cls
