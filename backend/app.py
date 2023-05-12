from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Union, Type
import pickle
import pandas as pd
import numpy as np
import json
import copy

import dice_ml
import gamcoach

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


# create aliases for the long class names
GamCoachCF = gamcoach.Counterfactuals
DiceMLCF = dice_ml.counterfactual_explanations.CounterfactualExplanations


# load my coach
with open('./my_coach.pickle', 'rb') as f:
    mynew_coach = pickle.load(f)

with open('./dice-model-customer.pickle', 'rb') as f:
    dice_model = pickle.load(f)

# Load the dataset
with open("customer-classifier-random-samples.json") as f:
    dataset = json.load(f)

# column names from the dataset
COLUMNS = mynew_coach.feature_names[:19]
TARGET = "churn"

class CFResponse:
    def __init__(self, cf: Union[GamCoachCF, DiceMLCF]):
        # check if cf is dice or coach
        self.process_counterfactuals(cf)
    
    
    def process_counterfactuals(self, cf: Union[GamCoachCF, DiceMLCF]):
        if isinstance(cf, GamCoachCF):
            self.data = cf.data
            active_variables = [a_var for a_var, _ in cf.solutions]
            # for each sublist in main list,  keep sublist with only items  without '_x_' in name
            self.active_variables = [[str(item) for item in sublist if '_x_' not in item.name]
                                      for sublist in active_variables]

            self.is_successful = True if len(self.active_variables) > 0 else False

        elif isinstance(cf, DiceMLCF):
            self.data = cf.cf_examples_list[0].final_cfs_df.drop(TARGET, axis=1).values
            self.active_variables = get_active_vars(cf)
            self.is_successful = True if len(self.data) > 0 else False


    def get_response(self):
        serialized_data = {
            'data': self.data.tolist(),
            'activeVariables': list(self.active_variables),
            'isSuccessful': self.is_successful
        }
        if len(self.data) > 1:
            serialized_data = [
            {
                'activeVariables': active_vars,
                'data': [data_item],
                'isSuccessful': serialized_data['isSuccessful']
            }
            for active_vars, data_item in zip(serialized_data['activeVariables'], serialized_data['data'])
        ]
        return serialized_data


def get_active_vars(exp):
    li = exp.cf_examples_list[0].final_cfs_df.drop(columns=['churn']).values
    newli = copy.deepcopy(li)
    org = exp.cf_examples_list[0].test_instance_df.drop(columns=['churn']).values.tolist()[0]
    combined = []
    columns = exp.cf_examples_list[0].final_cfs_df.columns
    for ix in range(len(newli)):
        active_vars = []
        for jx in range(len(newli[ix])):
            if newli[ix][jx] != org[jx]:
                active_vars.append(f"{columns[jx]}:{newli[ix][jx]}")
        combined.append(active_vars)
    return combined

def generate_counterfactuals(
        input_data, 
        total_CFs,
        continuous_integer_features,
        max_num_features_to_vary,
        features_to_vary,
        feature_ranges,
        explainer="coach"
        ):
    columns = COLUMNS
    if not isinstance(input_data, pd.DataFrame):
        input_data = pd.DataFrame(
            [input_data], 
            columns=columns, 
            )
        input_data[['tenure','monthlycharges', 'totalcharges']] = input_data[['tenure', 'monthlycharges', 'totalcharges']].astype(float)
    if explainer == "coach":
        explainer = mynew_coach
        cfs = explainer.generate_cfs(
            cur_example = input_data.values,
            total_cfs=total_CFs,
            feature_ranges=feature_ranges,
            features_to_vary=features_to_vary,
            max_num_features_to_vary=max_num_features_to_vary,
            continuous_integer_features=continuous_integer_features,
        )
    elif explainer == "dice":
        if features_to_vary is None:
            features_to_vary = 'all'
        explainer = dice_model
        cfs = explainer.generate_counterfactuals(
            query_instances = input_data,
            total_CFs=total_CFs,
            desired_class="opposite",
            features_to_vary=features_to_vary,
            permitted_range=feature_ranges,
            posthoc_sparsity_algorithm='binary',
        )
    return cfs


class RequestData(BaseModel):
    curExample: List[List[Union[str, int, float]]]
    cfMethod: str
    totalCfs: int
    continuousIntegerFeatures: List[Any]
    featuresToVary: Any  # Null (None) value is expected
    featureRanges: Dict[str, List[Any]]
    featureWeightMultipliers: Dict[str, float]
    verbose: int
    maxNumFeaturesToVary: int
    isNew: Any  # Null (None) value is expected



@app.post("/generate_counterfactuals")
async def generate_counterfactuals_endpoint(data: RequestData):
    print(data)
    total_cfs = 1 if data.isNew else 5

    counterfactuals = generate_counterfactuals(
        data.curExample[0], 
        total_cfs,
        data.continuousIntegerFeatures,
        data.maxNumFeaturesToVary,
        data.featuresToVary,
        data.featureRanges,
        explainer=data.cfMethod)
    response = CFResponse(counterfactuals).get_response()
    return response

@app.get("/dataset/{idx}")
async def get_example(idx: int):
    return dataset[idx]
