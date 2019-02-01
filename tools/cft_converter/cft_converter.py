from pcf.util import pcf_util
from copy import deepcopy
import json

base_particle = {
    "pcf_name": "PCF_NAME",
    "flavor": "FLAVOR",
    "parents": [],
    "aws_resource": {}
}


class Conversion:

    cft_field = None
    pcf_field = None

    def __init__(self, cft_def, particle_def):
        self.cft_def = cft_def
        self.particle_def = particle_def

    def convert(self):
        self.particle_def[self.__class__.pcf_field] = deepcopy(self.cft_def[self.__class__.cft_field])
        return self.particle_def


class PropertyConversion(Conversion):

    cft_field = "Properties"
    pcf_field = "aws_resource"


class RefConversion(Conversion):

    cft_field = "Ref"
    pcf_field = "lookup"

    def convert(self):
        var_list = pcf_util.find_nested_keys(self.particle_def,"Ref")
        for (nested_key, var) in var_list:
            nested_key_list = nested_key.split('.')
            nested_key_list.pop()
            self.particle_def = pcf_util.replace_value_nested_dict(self.particle_def,nested_key_list,"$lookup$RESOURCE$"+var)
        return self.particle_def


class MapConversion(Conversion):

    cft_field="Fn::FindInMap"
    pcf_field="lookup"

    def convert(self):
        var_list = pcf_util.find_nested_keys(self.particle_def,"Fn::FindInMap")
        for (nested_key, var) in var_list:
            nested_key_list = nested_key.split('.')
            nested_key_list.pop()
            self.particle_def = pcf_util.replace_value_nested_dict(self.particle_def,nested_key_list,"$lookup$RESOURCE$"+var)
        return self.particle_def


class DependsConversion(Conversion):

    cft_field="DependsOn"
    pcf_field="parents"

    def convert_temp_pcf_id(self, name):
        return "PARENT_FLAVOR:" + name

    def convert(self):
        parents = self.cft_def["DependsOn"]
        if isinstance(parents, str):
            renamed_parents = [self.convert_temp_pcf_id(parents)]
        else:
            renamed_parents = list(map(self.convert_temp_pcf_id,parents))

        self.particle_def["parents"]= renamed_parents
        return self.particle_def


class ConvertResource:

    CONVERSIONS = [
        PropertyConversion,
        RefConversion,
        MapConversion,
        DependsConversion
    ]

    def __init__(self, cft_resource):
        self.particle = base_particle
        self.cft = cft_resource

    def convert_fields(self, conversions="all"):
        for conversion in self.CONVERSIONS:
            if conversion.cft_field in conversions or conversions == 'all':
                self.particle = conversion(self.cft, self.particle).convert()

    def export_json(self, filename='pcf.json'):
        with open(filename, 'w') as file:
            json.dump(self.particle, file)
