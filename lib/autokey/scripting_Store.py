class Store(dict):
    """
    Allows persistent storage of values between invocations of the script.
    """
    
    def set_value(self, key, value):
        """
        Store a value
        
        Usage: C{store.set_value(key, value)}
        """
        self[key] = value
        
    def get_value(self, key):
        """
        Get a value
        
        Usage: C{store.get_value(key)}
        """
        return self.get(key, None)        
        
    def remove_value(self, key):
        """
        Remove a value
        
        Usage: C{store.remove_value(key)}
        """
        del self[key]
        
    def set_global_value(self, key, value):
        """
        Store a global value
        
        Usage: C{store.set_global_value(key, value)}
        
        The value stored with this method will be available to all scripts.
        """
        Store.GLOBALS[key] = value
        
    def get_global_value(self, key):
        """
        Get a global value
        
        Usage: C{store.get_global_value(key)}
        """
        return self.GLOBALS.get(key, None)        
        
    def remove_global_value(self, key):
        """
        Remove a global value
        
        Usage: C{store.remove_global_value(key)}
        """
        del self.GLOBALS[key]
        
    def has_key(self, key):
        """
        python 2 compatibility
        """
        return key in self
