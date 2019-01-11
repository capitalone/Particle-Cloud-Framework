
class Field:
    def __init__(self, cft, cft_key):
        self.extarcted_value = self.extract(cft,cft_key)
        self.pcf_obj = self.conversion(self.extarcted_value)

    def extract(self,cft, cft_tag):
        for key,value in cft.items():
            if key == cft_tag:
                return value

    def conversion(self,cft_value):
        return cft_value


class ParticleField(Field):
    def __init__(self):
        self.aws_resource = Field(self.cft,"Properties")
        self.pcf_name = Field()
        self.flavor = Field()
