class NoDataToPopulateVisualizations(Exception):

    def __init__(self):
        self.message = "No data to populate visualizations"
        super().__init__(self.message)
