import xml.etree.cElementTree as ElementTree

CONFIG_FILE = "../../config/config.xml"

NAME_ATTRIB = "name"
TYPE_ATTRIB = "type"
VALUE_ATTRIB = "value"

STRING_TYPE = "string"
BOOL_TYPE = "boolean"

TRUE_VALUE = "true"
FALSE_VALUE = "false"

SETTINGS_SECTION = "settings"
ABBR_DEFAULTS_SECTION = "abbr-defaults"

OPTION_ELEM = "option"

class ConfigurationService:
    
    def __init__(self):
        # TODO handle xml and file exceptions
        self.xml = ElementTree.parse(CONFIG_FILE)
        
    def get_setting(self, settingName):
        settingsElem = self.xml.find(SETTINGS_SECTION)
        for elem in list(settingsElem):
            if elem.attrib[NAME_ATTRIB] == settingName:
                name, value = self.__parseOption(elem)
                return value
        
    def get_abbreviation_defaults(self):
        elem = self.xml.find(ABBR_DEFAULTS_SECTION)
        return self.__readAbbrContext(elem)
    
    def get_abbr_contexts(self):
        """
        @deprecated: temporary method; to be removed once folders are implemented
        """
        return self.xml.findall("./abbr-folder/abbreviation")
    
    def get_abbr_settings(self, abbrContext):
        return self.__readAbbrContext(abbrContext)
    
    def finalise(self):
        del(self.xml)
        
    def __readAbbrContext(self, abbrContext):
        itemList = []
        for optionElem in list(abbrContext):
            itemList.append(self.__parseOption(optionElem))
        return dict(itemList)        
    
    def __parseOption(self, optionCtx):
        name = optionCtx.attrib[NAME_ATTRIB]
        type = optionCtx.attrib[TYPE_ATTRIB]
        if type == STRING_TYPE:
            value = optionCtx.attrib[VALUE_ATTRIB]
        else:
            value = (optionCtx.attrib[VALUE_ATTRIB] == TRUE_VALUE)
            
        return (name, value)