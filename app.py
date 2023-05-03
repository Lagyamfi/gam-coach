from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union, List
import pickle
import pandas as pd
import numpy as np
import json

app = FastAPI()

# Allow CORS
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# load my coach
with open('./my_coach.pickle', 'rb') as f:
    mynew_coach = pickle.load(f)

# Load the dataset
with open("customer-classifier-random-samples.json") as f:
    dataset = json.load(f)

# column names from the dataset
COLUMNS = mynew_coach.feature_names[:19]

class cf_response:
    def __init__(self, cf):
        self.data = cf.data
        active_variables = [a_var for a_var, _ in cf.solutions]
        # for each sublist in main list,  keep sublist with only items  without '_x_' in name
        self.active_variables = [[str(item) for item in sublist if '_x_' not in item.name] for sublist in active_variables]

        self.is_successful = True if len(self.active_variables) > 0 else False

    def get_response(self):
        serialized_data = {
            'data': self.data.tolist(),
            'activeVariables': list(self.active_variables),
            'isSuccessful': self.is_successful
        }
        return serialized_data


def generate_counterfactuals(input_data, explainer=mynew_coach):
    columns = COLUMNS
    if not isinstance(input_data, pd.DataFrame):
        # input_data = pd.DataFrame.from_dict([input_data], orient='columns')
        input_data = pd.DataFrame([input_data], columns=columns)
    cfs = explainer.generate_cfs(
        input_data.values,
        total_cfs=1,
        max_num_features_to_vary=np.random.randint(1, 3),
        continuous_integer_features=['tenure', ]
    )
    return cfs


test_cf = {
  "activeVariables": [["internetservice:0", "monthlycharges:210"]],
  "data": [["female", "no", "no", "no", 29, "yes", "yes", "dsl", "no", "no", "yes", "no", "yes", "yes", "month-to-month", "no", "bank_transfer_(automatic)", 97.82489999999999, 2878.75]],
  "isSuccessful": True
}

class InputDataDict(BaseModel):
    gender: str
    seniorcitizen: str
    partner: str
    dependents: str
    tenure: int
    phoneservice: str
    multiplelines: str
    internetservice: str
    onlinesecurity: str
    onlinebackup: str
    deviceprotection: str
    techsupport: str
    streamingtv: str
    streamingmovies: str
    contract: str
    paperlessbilling: str
    paymentmethod: str
    monthlycharges: float
    totalcharges: Union[float, str]

class InputData(BaseModel):
    inputData: list
    numCounterfactuals: int

# @app.post("/generate_counterfactuals")
# async def generate_counterfactuals_endpoint(input_data: InputData):
#     print(input_data.data)
#     # counterfactuals = generate_counterfactuals(input_data.dict())
#     #counterfactuals = generate_counterfactuals(input_data.data)
#     #return {"counterfactuals": counterfactuals}

#     serialized_data = {
#         "activeVariables": [["internetservice:0", "monthlycharges:210"]] * input_data.numCounterfactuals,
#         "data": [
#             [
#                 "female",
#                 "no",
#                 "no",
#                 "no",
#                 29,
#                 "yes",
#                 "yes",
#                 "dsl",
#                 "no",
#                 "no",
#                 "yes",
#                 "no",
#                 "yes",
#                 "yes",
#                 "month-to-month",
#                 "no",
#                 "bank_transfer_(automatic)",
#                 97.82489999999999,
#                 2878.75,
#             ]
#             for _ in range(input_data.numCounterfactuals)
#         ],
#         "isSuccessful": True,
#     }
#     return serialized_data

@app.get("/generate_counterfactuals")
async def generate_counterfactuals_endpoint():
    counterfactuals = generate_counterfactuals(dataset[0])
    response = cf_response(counterfactuals).get_response()
    return response


@app.get("/dataset/{idx}")
async def get_example(idx: int):
    return dataset[idx]
