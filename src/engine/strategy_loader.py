import importlib.util
import sys
import os

def load_strategy(strategy_path):
    """
    Dynamically load a Python strategy module from a file path.
    
    The strategy module must contain a Strategy class with a generate_signal method.
    
    Args:
        strategy_path: Path to the Python file containing the strategy
    
    Returns:
        Instance of the Strategy class from the loaded module
    
    Raises:
        ValueError: If strategy file doesn't exist or doesn't contain required class
    """
    if not os.path.exists(strategy_path):
        raise ValueError(f"Strategy file not found: {strategy_path}")
    
    if not strategy_path.endswith('.py'):
        raise ValueError("Strategy file must be a Python (.py) file")
    
    try:
        # Get the module name from the file path
        module_name = os.path.splitext(os.path.basename(strategy_path))[0]
        
        # Load the module from file
        spec = importlib.util.spec_from_file_location(module_name, strategy_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Failed to load module spec from {strategy_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Check if the module has a Strategy class
        if not hasattr(module, 'Strategy'):
            raise ValueError(f"Strategy file must contain a 'Strategy' class")
        
        strategy_class = getattr(module, 'Strategy')
        
        # Instantiate and return the strategy
        strategy_instance = strategy_class()
        
        # Verify the strategy has required methods
        if not hasattr(strategy_instance, 'generate_signal'):
            raise ValueError("Strategy class must implement 'generate_signal' method")
        
        return strategy_instance
        
    except Exception as e:
        raise ValueError(f"Error loading strategy: {e}")
