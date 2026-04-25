#router file for getting domains
from agent.pipelines.math_pipe import solve as solve_math
from agent.pipelines.coding_pipe import solve as solve_coding
from agent.pipelines.common_sense_pipe import solve as solve_common_sense
from agent.pipelines.planning_pipe import solve as solve_planning
from agent.pipelines.future_prediction_pipe import solve as solve_future_prediction

def guess_domain(question_text):
    #simple way to get the domain from keywords
    text = (question_text or "").lower()
    if "[plan]" in text or "my plan is as follows" in text:
        return "planning"
    if "write self-contained code" in text or "def task_func" in text:
        return "coding"
    if "predict future events" in text:
        return "future_prediction"
    if "$" in text or "\\sqrt" in text or "equation" in text:
        return "math"
    return "common_sense"

def get_domain(item):
    #small helper so the rest of the code can ask for the domain in one place, 
    #since we'll have more now
    if "domain" in item and item["domain"]:
        return item["domain"]
    question_text = item.get("input", "")
    return guess_domain(question_text)

def route_item(item):
    #return the final answer from the correct pipeline file
    domain = get_domain(item)
    question_text = item.get("input", "")
    if domain == "math":
        return solve_math(question_text)
    if domain == "coding":
        return solve_coding(question_text)
    if domain == "planning":
        return solve_planning(question_text)
    if domain == "future_prediction":
        return solve_future_prediction(question_text)
    return solve_common_sense(question_text)

if __name__ == "__main__":
    sample_item = {"input": "Which magazine was started first Arthur's Magazine or First for Women?"}
    print("guessed domain:", get_domain(sample_item))
    print("pipeline output:", route_item(sample_item))
