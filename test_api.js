const input_data = {
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
};

fetch('http://127.0.0.1:8000/generate_counterfactuals', {
    method: 'POST',
    body: JSON.stringify(input_data),
    headers: {
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error(error));
