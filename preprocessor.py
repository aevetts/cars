import numpy as np
import pandas as pd

class TextEncoder:
    def __init__(self):
        self.vocabs = {}
        self.features = []

    def fit(self, dataframe, columns):
        # Fit the encoder by building vocabularies for the specified categorical features.
        self.features = columns
        for col in columns:
            unique_values = dataframe[col].dropna().unique()
            self.vocabs[col] = {val: i+1 for i, val in enumerate(sorted(unique_values))}

    def transform_df(self, dataframe):
        # Transform a dataframe into a dictionary of arrays using the fitted vocabularies (only the fitted features).
        transformed = {}
        for col in self.features:
            transformed[col] = dataframe[col].map(self.vocabs[col]).fillna(0).astype('int32').values
        return transformed
    
    # def save_json(self, filename):
    #     # Save the vocabularies to a JSON file for later use in the app dropdowns.
    #     import json
    #     with open(filename, 'w') as f:
    #         json.dump(self.vocabs, f)