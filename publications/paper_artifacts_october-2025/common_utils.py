from pprint import pprint
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

# compute average scores and sd per proposition (use some well-known lib to compute statistics)
def compute_average_scores(scores):
    average_scores = {}
    for k, v in scores.items():
        average_scores[k] = {
            "mean": sum(v) / len(v),
            "sd": pd.Series(v).std(),
            "n": len(v)
        }
    return average_scores

def plot_scores(propositions_scores):
    pprint(propositions_scores)
    
    propositions_scores_stats = compute_average_scores(propositions_scores)

    # build a pandas dataframe with average scores per proposition
    df = pd.DataFrame(propositions_scores_stats).T
    df = df.rename(columns={"mean": "Average Score", "sd": "Standard Deviation", "n": "Count"})
    df = df.reset_index()
    df = df.rename(columns={"index": "Proposition"})
    
    display(df)

def merge_dicts_of_lists(source_dict, target_dict):
    """
    Merges the contents of source_dict into a clone of target_dict.
    If a key is not present in the clone, it initializes an empty list.
    Appends the values from source_dict to the corresponding key in the clone.
    Returns the merged clone.
    """
    merged_dict = target_dict.copy()  # Clone the target_dict
    for key, value in source_dict.items():
        if key not in merged_dict:
            merged_dict[key] = []
        merged_dict[key].extend(value)
    return merged_dict