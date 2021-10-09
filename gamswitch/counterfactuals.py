"""Counterfactuals Class.

This module implements the Counterfactuals class. We use it to represent the
generated counterfactual explanations.
"""

import numpy as np
import pandas as pd
import re
import pulp

from tqdm import tqdm
from interpret.glassbox import ExplainableBoostingClassifier, ExplainableBoostingRegressor
from time import time
from collections import Counter
from typing import Union

SEED = 922


class Counterfactuals:
    """Class to represent GAM counterfactual explanations."""

    def __init__(self,
                 solutions: list,
                 isSuccessful: bool,
                 model: pulp.LpProblem,
                 variables: dict,
                 ebm: Union[ExplainableBoostingClassifier, ExplainableBoostingRegressor],
                 cur_example: np.ndarray,
                 options: dict):
        """Initialize a Counterfactuals object.

        Args:
            solutions (list): List of generated `(active_variables, optimal value)`.
                If successful, it should have `total_cfs` items.
            isSuccessful (bool): True if the mixed-integer linear problem has
                `total_cfs` number of solutions under all constraints.
            model (LpProblem): Linear programming model
            variables (dict): Dictionary containing all MILP variables,
                `feature_name` -> [`variables`],
            ebm (Union[ExplainableBoostingClassifier, ExplainableBoostingRegressor]):
                The trained EBM model.
            cur_example (np.ndarray): The original data point.
            options (dict): Dictionary containing all eligible options for each
                selected features. `feature_name` -> `[[target, score_gain,
                distance, bin_id]]`
        """
        self.isSuccessful = isSuccessful
        """Boolean to indicate if the optimization is successful."""

        self.model = model
        """MILP program model."""

        self.variables = variables
        """MILP program variabels."""

        self.ebm = ebm
        """The trained EBM model."""

        self.cur_example = cur_example[0]
        """The original data point."""

        self.options = options
        """All possible options."""

        self.data: np.ndarray
        """Generated CFs in the original data dataformat."""

        self.target_bins: list
        """New bins used in each row of `data`."""

        self.values: list
        """Cooresponding objective values (total distance) of each `data` row."""

        self.convert_cfs_to_data(solutions)

    def convert_cfs_to_data(self, solutions):
        """Convert optimal CF solutions to the original dataformat.
        """

        self.data = []
        self.values = []
        self.target_ranges = []

        for active_variables, value in solutions:
            cur_cf = self.cur_example.copy()
            cur_target_ranges = []

            for var in active_variables:
                # Skip interaction vars (included)
                if 'x' not in var.name:
                    f_name = re.sub(r'(.+):\d+', r'\1', var.name)
                    bin_i = int(re.sub(r'.+:(\d+)', r'\1', var.name))

                    # Find the original value
                    org_value = self.cur_example[self.ebm.feature_names.index(f_name)]

                    # Find the target bin
                    f_index = self.ebm.feature_names.index(f_name)
                    f_type = self.ebm.feature_types[f_index]

                    if f_type == 'continuous':
                        bin_starts = self.ebm.preprocessor_._get_bin_labels(f_index)[:-1]

                        target_bin = '[{},'.format(bin_starts[bin_i])

                        if bin_i + 1 < len(bin_starts):
                            target_bin += ' {})'.format(bin_starts[bin_i + 1])
                        else:
                            target_bin += ' inf)'
                    else:
                        target_bin = ''
                        org_value = '"{}"'.format(org_value)


                    for option in self.options[f_name]:
                        if option[3] == bin_i:
                            target_value = option[0]
                            cur_cf[f_index] = target_value

                            if f_type == 'continuous':
                                cur_target_ranges.append(target_bin)
                            else:
                                cur_target_ranges.append(option[0])
                            break

            self.data.append(cur_cf)
            self.values.append(value)
            self.target_ranges.append(cur_target_ranges)

        self.data = np.vstack(self.data)

    def model_summary(self):
        """Print out a summary of the MILP model."""
        print('MILP model with {} variables and {} constraints.'.format(
            self.model.numVariables(),
            self.model.numConstraints()
        ))

        print(self.data)
        print(self.target_ranges)
        print(self.values)
