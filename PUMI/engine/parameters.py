import re
import ast
from hashlib import sha1

class ParameterCollector:
    """
    A class to collect and store parameters used in the pipeline.
    
    This class collects parameters from two main sources:
    1. settings.ini file (via cfg_parser)
    2. Workflow nodes and their interfaces
    
    The collected parameters are stored in a structured format and are automatically
    converted to JSON-serializable values.
    """
    def __init__(self, wf):
        """
        Initialize the ParameterCollector.
        
        Args:
            wf: The workflow object containing the configuration parser and nodes.
        """
        self.wf = wf
        self.parameters = {
            'settings': {},  # Parameters from settings.ini
            'workflow': {}   # Parameters from workflow nodes
        }
        
    def _is_undefined(self, value):
        """
        Check if a value is an Undefined trait value.
        
        Args:
            value: The value to check
            
        Returns:
            bool: True if the value is undefined, False otherwise
        """
        return str(type(value)).endswith("._Undefined'>")
        
    def _convert_value(self, value):
        """
        Convert a value to a JSON-serializable format.
        
        Args:
            value: The value to convert
            
        Returns:
            The converted value that is JSON-serializable
        """
        if value is None or self._is_undefined(value):
            return None
        elif isinstance(value, Path):
            return str(value)
        elif hasattr(value, '__module__') and 'matplotlib' in str(value.__module__):
            return str(value)  # Convert matplotlib objects to strings
        elif hasattr(value, 'trait_type'):  # Handle CTrait objects
            try:
                if hasattr(value, 'value'):
                    actual_value = value.value
                elif hasattr(value, 'get'):
                    actual_value = value.get()
                else:
                    actual_value = value
                return self._convert_value(actual_value)  # Recursively convert the actual value
            except (AttributeError, TypeError):
                return str(value)
        elif hasattr(value, '__dict__'):
            # For objects with __dict__, try to get their string representation
            return str(value)
        return value
        
    def _is_empty(self, value):
        """
        Check if a value is empty or contains only empty values.
        
        Args:
            value: The value to check
            
        Returns:
            bool: True if the value is empty, False otherwise
        """
        if value is None:
            return True
        elif isinstance(value, (list, tuple, set)):
            return len(value) == 0
        elif isinstance(value, dict):
            return all(self._is_empty(v) for v in value.values())
        return False
        
    def collect_from_settings(self):
        """
        Collect parameters from settings.ini file.
        
        This method reads all sections and their key-value pairs from the config parser,
        converts the values to JSON-serializable format, and stores them in the settings
        dictionary. Empty sections are removed.
        """
        if not hasattr(self.wf, 'cfg_parser'):
            return
            
        try:
            for section in self.wf.cfg_parser.sections():
                self.parameters['settings'][section] = {}
                for key, value in self.wf.cfg_parser.items(section):
                    converted_value = self._convert_value(value)
                    if not self._is_empty(converted_value):
                        self.parameters['settings'][section][key] = converted_value
                        
                # Remove empty sections
                if not self.parameters['settings'][section]:
                    del self.parameters['settings'][section]
        except Exception as e:
            print(f"Warning: Error collecting settings parameters: {e}")
                
    def collect_from_workflow(self):
        """
        Collect parameters from workflow nodes.
        
        This method iterates through all nodes in the workflow, collects their input
        parameters, converts them to JSON-serializable format, and stores them in the
        workflow dictionary. Empty nodes are removed.
        """
        try:
            for node_name in self.wf.list_node_names():
                node = self.wf.get_node(node_name)
                if hasattr(node, 'interface') and hasattr(node.interface, 'inputs'):
                    self.parameters['workflow'][node_name] = {}
                    # Get the actual input values that were set
                    for trait_name, trait in node.interface.inputs.traits().items():
                        if trait_name in node.interface.inputs.__dict__:
                            value = node.interface.inputs.__dict__[trait_name]
                            converted_value = self._convert_value(value)
                            if not self._is_empty(converted_value):
                                self.parameters['workflow'][node_name][trait_name] = converted_value
                                
                    # Remove empty nodes
                    if not self.parameters['workflow'][node_name]:
                        del self.parameters['workflow'][node_name]
        except Exception as e:
            print(f"Warning: Error collecting workflow parameters: {e}")
                        
    def collect_all(self):
        """
        Collect all parameters from various sources.
        
        Returns:
            dict: A dictionary containing all collected parameters, organized by source
        """
        self.collect_from_settings()
        self.collect_from_workflow()
        return self.parameters