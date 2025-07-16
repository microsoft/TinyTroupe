import json
import copy
from pydantic import BaseModel

from tinytroupe.utils import logger

class JsonSerializableRegistry:
    """
    A mixin class that provides JSON serialization, deserialization, and subclass registration.
    """
    
    class_mapping = {}

    def to_json(self, include: list = None, suppress: list = None, file_path: str = None,
                serialization_type_field_name = "json_serializable_class_name") -> dict:
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
        custom_serializers = {}
        for cls in self.__class__.__mro__:  # Traverse the class hierarchy
            if hasattr(cls, 'serializable_attributes') and isinstance(cls.serializable_attributes, list):
                serializable_attrs.update(cls.serializable_attributes)
            if hasattr(cls, 'suppress_attributes_from_serialization') and isinstance(cls.suppress_attributes_from_serialization, list):
                suppress_attrs.update(cls.suppress_attributes_from_serialization)
            if hasattr(cls, 'custom_serializers') and isinstance(cls.custom_serializers, dict):
                custom_serializers.update(cls.custom_serializers)
        
        # Override attributes with method parameters if provided
        if include:
            serializable_attrs = set(include)
        if suppress:
            suppress_attrs.update(suppress)
        
        def aux_serialize_item(item):
            if isinstance(item, JsonSerializableRegistry):
                return item.to_json(serialization_type_field_name=serialization_type_field_name)
            elif isinstance(item, BaseModel):
                # If it's a Pydantic model, convert it to a dict first
                logger.debug(f"Serializing Pydantic model: {item}")
                return item.model_dump(mode="json", exclude_unset=True)
            else:
                return copy.deepcopy(item)
        
        result = {serialization_type_field_name: self.__class__.__name__}
        for attr in serializable_attrs if serializable_attrs else self.__dict__:
            if attr not in suppress_attrs:
                value = getattr(self, attr, None)

                attr_renamed = self._programmatic_name_to_json_name(attr)
                
                # Check if there's a custom serializer for this attribute
                if attr in custom_serializers:
                    result[attr_renamed] = custom_serializers[attr](value)
                elif isinstance(value, list):
                    result[attr_renamed] = [aux_serialize_item(item) for item in value]
                elif isinstance(value, dict):
                    result[attr_renamed] = {k: aux_serialize_item(v) for k, v in value.items()}
                else: # isinstance(value, JsonSerializableRegistry) or isinstance(value, BaseModel) or other types
                    result[attr_renamed] = aux_serialize_item(value)

        if file_path:
            # Create directories if they do not exist
            import os
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(result, f, indent=4)
        
        return result

    @classmethod
    def from_json(cls, json_dict_or_path, suppress: list = None, 
                  serialization_type_field_name = "json_serializable_class_name", 
                  post_init_params: dict = None):
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
        
        subclass_name = json_dict.get(serialization_type_field_name)
        target_class = cls.class_mapping.get(subclass_name, cls)
        instance = target_class.__new__(target_class)  # Create an instance without calling __init__
        
        # Gather all serializable attributes from the class hierarchy
        serializable_attrs = set()
        custom_deserializers = {}
        suppress_attrs = set(suppress) if suppress else set()
        for target_mro in target_class.__mro__:
            if hasattr(target_mro, 'serializable_attributes') and isinstance(target_mro.serializable_attributes, list):
                serializable_attrs.update(target_mro.serializable_attributes)
            if hasattr(target_mro, 'custom_deserializers') and isinstance(target_mro.custom_deserializers, dict):
                custom_deserializers.update(target_mro.custom_deserializers)
            if hasattr(target_mro, 'suppress_attributes_from_serialization') and isinstance(target_mro.suppress_attributes_from_serialization, list):
                suppress_attrs.update(target_mro.suppress_attributes_from_serialization)
        
        # Assign values only for serializable attributes if specified, otherwise assign everything
        for key in serializable_attrs if serializable_attrs else json_dict:
            key_in_json = cls._programmatic_name_to_json_name(key)
            if key_in_json in json_dict and key not in suppress_attrs:
                value = json_dict[key_in_json]
                if key in custom_deserializers:
                    # Use custom initializer if provided
                    setattr(instance, key, custom_deserializers[key](value))
                elif isinstance(value, dict) and serialization_type_field_name in value:
                    # Assume it's another JsonSerializableRegistry object
                    setattr(instance, key, JsonSerializableRegistry.from_json(value, serialization_type_field_name=serialization_type_field_name))
                elif isinstance(value, list):
                    # Handle collections, recursively deserialize if items are JsonSerializableRegistry objects
                    deserialized_collection = []
                    for item in value:
                        if isinstance(item, dict) and serialization_type_field_name in item:
                            deserialized_collection.append(JsonSerializableRegistry.from_json(item, serialization_type_field_name=serialization_type_field_name))
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
        
        if hasattr(cls, 'custom_deserializers') and isinstance(cls.custom_deserializers, dict):
            for base in cls.__bases__:
                if hasattr(base, 'custom_deserializers') and isinstance(base.custom_deserializers, dict):
                    base_initializers = base.custom_deserializers.copy()
                    base_initializers.update(cls.custom_deserializers)
                    cls.custom_deserializers = base_initializers
        
        if hasattr(cls, 'custom_serializers') and isinstance(cls.custom_serializers, dict):
            for base in cls.__bases__:
                if hasattr(base, 'custom_serializers') and isinstance(base.custom_serializers, dict):
                    base_serializers = base.custom_serializers.copy()
                    base_serializers.update(cls.custom_serializers)
                    cls.custom_serializers = base_serializers

    def _post_deserialization_init(self, **kwargs):
        # if there's a _post_init method, call it after deserialization
        if hasattr(self, '_post_init'):
            self._post_init(**kwargs)

    @classmethod
    def _programmatic_name_to_json_name(cls, name):
        """
        Converts a programmatic name to a JSON name by converting it to snake case.
        """
        if hasattr(cls, 'serializable_attributes_renaming') and isinstance(cls.serializable_attributes_renaming, dict):
            return cls.serializable_attributes_renaming.get(name, name)
        return name
    
    @classmethod
    def _json_name_to_programmatic_name(cls, name):
        """
        Converts a JSON name to a programmatic name.
        """
        if hasattr(cls, 'serializable_attributes_renaming') and isinstance(cls.serializable_attributes_renaming, dict):
            reverse_rename = {}
            for k, v in cls.serializable_attributes_renaming.items():
                if v in reverse_rename:
                    raise ValueError(f"Duplicate value '{v}' found in serializable_attributes_renaming.")
                reverse_rename[v] = k
            return reverse_rename.get(name, name)
        return name

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

def merge_dicts(current, additions, overwrite=False, error_on_conflict=True, remove_duplicates=True):
    """
    Merges two dictionaries and returns a new dictionary. Works as follows:
    - If a key exists in the additions dictionary but not in the current dictionary, it is added.
    - If a key maps to None in the current dictionary, it is replaced by the value in the additions dictionary.
    - If a key exists in both dictionaries and the values are dictionaries, the function is called recursively.
    - If a key exists in both dictionaries and the values are lists, the lists are concatenated and duplicates are removed
      (if remove_duplicates is True).
    - If the values are of different types, an exception is raised.
    - If the values are of the same type but not both lists/dictionaries, the value from the additions dictionary overwrites the value in the current dictionary based on the overwrite parameter.
    
    Parameters:
    - current (dict): The original dictionary.
    - additions (dict): The dictionary with values to add.
    - overwrite (bool): Whether to overwrite values if they are of the same type but not both lists/dictionaries.
    - error_on_conflict (bool): Whether to raise an error if there is a conflict and overwrite is False.
    - remove_duplicates (bool): Whether to remove duplicates from lists when merging.
    
    Returns:
    - dict: A new dictionary with merged values.
    """
    merged = current.copy()  # Create a copy of the current dictionary to avoid altering it

    for key in additions:
        if key in merged:
            # If the current value is None, directly assign the new value
            if merged[key] is None:
                merged[key] = additions[key]
            # If both values are dictionaries, merge them recursively
            elif isinstance(merged[key], dict) and isinstance(additions[key], dict):
                merged[key] = merge_dicts(merged[key], additions[key], overwrite, error_on_conflict)
            # If both values are lists, concatenate them and remove duplicates
            elif isinstance(merged[key], list) and isinstance(additions[key], list):
                merged[key].extend(additions[key])
                # Remove duplicates while preserving order
                if remove_duplicates:
                    merged[key] = remove_duplicate_items(merged[key])
            # If the values are of different types, raise an exception
            elif type(merged[key]) != type(additions[key]):
                raise TypeError(f"Cannot merge different types: {type(merged[key])} and {type(additions[key])} for key '{key}'")
            # If the values are of the same type but not both lists/dictionaries, decide based on the overwrite parameter
            else:
                if overwrite:
                    merged[key] = additions[key]
                elif merged[key] != additions[key]:
                    if error_on_conflict:
                        raise ValueError(f"Conflict at key '{key}': overwrite is set to False and values are different.")
                    else:
                        continue  # Ignore the conflict and continue
        else:
            # If the key is not present in merged, add it from additions
            merged[key] = additions[key]

    return merged

def remove_duplicate_items(lst):
        """
        Removes duplicates from a list while preserving order.
        Handles unhashable elements by using a list comprehension.

        Parameters:
        - lst (list): The list to remove duplicates from.

        Returns:
        - list: A new list with duplicates removed.
        """
        seen = []
        result = []
        for item in lst:
            if isinstance(item, dict):
                # Convert dict to a frozenset of its items to make it hashable
                item_key = frozenset(item.items())
            else:
                item_key = item

            if item_key not in seen:
                seen.append(item_key)
                result.append(item)
        return result