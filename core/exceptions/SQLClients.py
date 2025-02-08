class CSQLInvalidQuery(Exception):

    def __init__(self, e: Exception):
        self.message = e.args[0]
        super().__init__(self.message)

