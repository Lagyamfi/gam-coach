from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union, List
import pickle
import pandas as pd
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

def generate_counterfactuals(input_data, explainer=mynew_coach):
    columns = COLUMNS
    if not isinstance(input_data, pd.DataFrame):
        # input_data = pd.DataFrame.from_dict([input_data], orient='columns')
        input_data = pd.DataFrame([input_data], columns=columns)
    cfs = explainer.generate_cfs(
        input_data.values,
        total_cfs=5,
        max_num_features_to_vary=3,
        continuous_integer_features=['tenure', ]
    )
    # return cfs.to_df().to_dict(orient='records')
    # return cfs.to_df().values.tolist()
    return cfs
    # return cfs

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
    data: List[Union[str, int, float]]

@app.post("/generate_counterfactuals")
async def generate_counterfactuals_endpoint(input_data: InputData):
    print(input_data.data)
    # counterfactuals = generate_counterfactuals(input_data.dict())
    counterfactuals = generate_counterfactuals(input_data.data)
    return {"counterfactuals": counterfactuals}

@app.get("/dataset/{idx}")
async def get_example(idx: int):
    return dataset[idx]
