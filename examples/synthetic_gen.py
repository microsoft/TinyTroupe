import json
import sys
import csv
sys.path.append('..')


import tinytroupe
from tinytroupe.agent import TinyPerson
from tinytroupe.environment import TinyWorld, TinySocialNetwork
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.extraction import ResultsReducer
import tinytroupe.control as control

factory = TinyPersonFactory("A random knowledge worker in a company providing marketing services.")

people = []
for i in range(2):
    person = factory.generate_person(temperature=1.6)
    print(person.minibio())
    people.append(person)

# len(people)

company = TinyWorld("Some Corp Inc.", people)
company.make_everyone_accessible()

company.broadcast("Get some work done together, help each other.")

company.run(5)


people[0].pp_current_interactions()

reducer = ResultsReducer()

def aux_extract_content(focus_agent: TinyPerson, source_agent:TinyPerson, target_agent:TinyPerson, kind:str, event: str, content: str, timestamp:str):

    if event == "TALK":
        author = focus_agent.name
    elif event == "CONVERSATION":
        if source_agent is None:
            author = "USER"
        else:
            author = source_agent.name
    else:
        raise ValueError(f"Unknown event: {event}")
    
    
    entry = (author, content)
    print(entry)
    return entry
    


reducer.add_reduction_rule("TALK", aux_extract_content)
reducer.add_reduction_rule("CONVERSATION", aux_extract_content)

df = reducer.reduce_agent_to_dataframe(people[0], column_names=["author", "content"])

print(df)

df.to_csv("../data/extractions/synthetic_data_generation.out.csv", index=False)