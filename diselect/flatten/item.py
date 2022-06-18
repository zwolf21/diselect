from ..utils.bases import ParameterBase



class FlatItem(ParameterBase):

    def __init__(self, index, path, value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index
        self.path = path
        self.value = value

    def __str__(self):
        kwargs = {
            k:str(v) for k, v in self.__dict__.items()
        }
        return 'INDEX: {index:<15} PATH: {path:<25} VALUE: {value:<20}'.format(**kwargs)




        