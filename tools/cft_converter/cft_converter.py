from pcf.util import pcf_util

base_particle = {
    "pcf_name":"PCF_NAME",
    "flavor":"FLAVOR",
    "parents":[],
    "aws_resource":{}
}


class Conversion:

    cft_field = None
    pcf_field = None

    def __init__(self, cft_def, particle_def):
        self.cft_def = cft_def
        self.particle_def = particle_def

    def convert(self):
        self.particle_def[self.__class__.pcf_field] = self.cft_def[self.__class__.cft_field]
        return self.particle_def


class PropertyConversion(Conversion):

    cft_field="Properties"
    pcf_field="aws_resource"


class RefConversion(Conversion):

    cft_field="Ref"
    pcf_field="lookup"

    def convert(self):
        var_list = pcf_util.find_nested_keys(self.cft_def,"Ref")
        for (nested_key, id_var) in var_list:
            if nested_key == "Ref":
                print(id_var)


class ConvertResource:

    CONVERSIONS= [
        PropertyConversion,
        RefConversion
    ]

    def __init__(self,cft_resource):
        self.particle = base_particle
        self.cft = cft_resource

    def convert_fields(self, conversions="all"):
        for conversion in self.CONVERSIONS:
            if conversion.cft_field in conversions or conversions == 'all':
                self.particle = conversion(self.cft, self.particle).convert()

