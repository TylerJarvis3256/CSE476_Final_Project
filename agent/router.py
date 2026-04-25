#router file for getting domains

def guess_domain(question_text):
    #simple way to get the domain from keywords
    text = (question_text or "").lower()
    if "[plan]" in text or "my plan is as follows" in text:
        return "planning"
    if "write self-contained code" in text or "def task_func" in text:
        return "coding"
    if "predict future events" in text:
        return "future_prediction"
    if "$" in question_text or "\\sqrt" in question_text or "equation" in text:
        return "math"
    return "common_sense"


def route_item(item):
    #return the domain name
    if "domain" in item and item["domain"]:
        return item["domain"]
    question_text = item.get("input", "")
    return guess_domain(question_text)
