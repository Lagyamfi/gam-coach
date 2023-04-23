from app import generate_counterfactuals
import pandas as pd

input_data = {
    'gender': 'female',
    'seniorcitizen': 'yes',
    'partner': 'no',
    'dependents': 'no',
    'tenure': 46,
    'phoneservice': 'yes',
    'multiplelines': 'yes',
    'internetservice': 'fiber_optic',
    'onlinesecurity': 'no',
    'onlinebackup': 'yes',
    'deviceprotection': 'yes',
    'techsupport': 'no',
    'streamingtv': 'yes',
    'streamingmovies': 'yes',
    'contract': 'month-to-month',
    'paperlessbilling': 'yes',
    'paymentmethod': 'electronic_check',
    'monthlycharges': 104.45,
    'totalcharges': 4863.85
}

input_data = pd.DataFrame.from_dict([input_data])
counterfactuals = generate_counterfactuals(input_data.values)
print(counterfactuals)
