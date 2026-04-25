import json
import sys
from agent.llm import get_call_count
from agent.llm import reset_call_count
from agent.router import route_item

#this is a simple runner for the full project shape
#each teammate pipeline file should have solve(input_text)

def load_input_file(path):
    #open the json file and turn it into python data
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if type(data) != list:
        print("input file should be a list")
        return []
    return data


def build_output_rows(items):
    #go item by item and save the final output in desired format
    rows = []
    call_log = []
    for i in range(len(items)):
        item = items[i]
        reset_call_count()
        error = ""
        final_output = ""
        try:
            final_output = route_item(item)
        except Exception as e:
            print("error on item", i, ":", e)
            error = str(e)
        if final_output is None:
            final_output = ""
        row = {"output": str(final_output)}
        rows.append(row)
        log_row = {
            "index": i,
            "calls": get_call_count(),
            "error": error
        }
        call_log.append(log_row)
    return rows, call_log


def save_output_file(path, rows):
    #write the output json so we can inspect it later
    with open(path, "w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)

def save_call_log(path, rows):
    #save the call log too so we can debug later
    with open(path, "w", encoding="utf-8") as file:
        json.dump(rows, file, indent=2)

#simple command line usage:
#python run_agent.py input.json output.json
def main():
    if len(sys.argv) < 3:
        print("python run_agent.py input.json output.json")
        return
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    items = load_input_file(input_path)
    rows, call_log = build_output_rows(items)
    save_output_file(output_path, rows)
    save_call_log("outputs/calls_log.json", call_log)
    print("done")
    print("items processed:", len(rows))
    print("last item call count:", get_call_count())

if __name__ == "__main__":
    main()
