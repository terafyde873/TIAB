import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import warnings

def main():
    # Suppress specific warnings from the transformers library
    warnings.filterwarnings("ignore", category=FutureWarning, message=".*clean_up_tokenization_spaces*")

    # Suppress logging messages from the transformers library
    logging.getLogger("transformers").setLevel(logging.ERROR)

    # Initialize the tokenizer and model
    model_name = "Salesforce/codegen-350M-mono"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    model.eval()

    # Read the user input from stdin
    user_input = sys.stdin.read().strip()
    if not user_input:
        return  # No input provided

    # Create a clear prompt for code generation
    prompt = f"Generate Python code for the following task:\n{user_input}\nPython code:"

    # Tokenize the prompt
    inputs = tokenizer(prompt, return_tensors="pt")

    # Generate a response
    with torch.no_grad():
        outputs = model.generate(
            inputs['input_ids'],
            max_length=150,  # Adjust based on expected output length
            num_return_sequences=1,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=2,  # Avoid repeating phrases
        )

    # Decode the response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Post-process the response to clean it up
    response_lines = response.strip().split('\n')
    # Ensure we capture only the code part
    code_lines = [line for line in response_lines if not line.startswith('Generate') and not line.startswith('Python code')]
    cleaned_response = '\n'.join(code_lines).strip()

    # Output only the cleaned code
    print(cleaned_response, flush=True)

if __name__ == "__main__":
    main()
