import streamlit as st
import pickle
import pandas as pd
import json

from preprocessor import TextEncoder

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model, callbacks

import numpy as np

@st.cache_resource
def load_model():
    return tf.keras.models.load_model('savedModels/noVariant.keras')

carmodel = load_model()


# Load the saved encoder
@st.cache_resource
def load_encoder():
    return pickle.load(open('encoder.pkl', 'rb'))
    
encoder = load_encoder()

# Load the dropdown data
@st.cache_data
def load_dropdown_data():
    with open('ui_assets.json', 'r') as f:
        return json.load(f)

dropdown_data = load_dropdown_data()


##########################################################################################
##########################################################################################
##########################################################################################

st.title('Alex\'s Car Price Predictor')


##########################################################################################
####### User inputs ######################################################################
##########################################################################################

col1, col2 = st.columns(2)


make = col1.selectbox('Make', (dropdown_data['make_model'].keys()) )
fuel = col1.selectbox('Fuel Type', (dropdown_data['fuel_types']))
mileage = col1.number_input('Mileage', min_value=0, max_value=500000, value=20000)


model = col2.selectbox('Model', (dropdown_data['make_model'][make]))
year = col2.number_input('Year', min_value=1900, max_value=2026, value=2015)
col2.space()

    # Encode the categorical inputs
cat_enc = encoder.transform_df(pd.DataFrame({'make': [make], 'model': [model], 'fuel_type': [fuel]}))

    # Combine the encoded categorical features with the numerical features
encoded_input = cat_enc | {'num_in': np.array([[mileage, year]], dtype='float32')}  

if col2.button("Predict"):
    logpred = carmodel.predict(encoded_input)
    truepred = np.exp(logpred)
    col1.write(f"The predicted price of this car is £{truepred[0][0]:,.2f}")

st.space("large")
st.markdown("Note: this is a learning project, based on a historic dataset, and was written by a beginner. Don't take the predictions too seriously! For more info, see the [blog](https://aevetts.github.io/streamlit/)")

##########################################################################################
####### Prediction #######################################################################
##########################################################################################











