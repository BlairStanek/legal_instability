import openai, anthropic, datetime, time
from google.oauth2 import service_account
import google.generativeai as genai

def log_messages(messages, model):
    rv = ""
    with open("calls.LOG", "a") as logfile:
        logfile.write("*******************************************\n")
        rv = str(datetime.datetime.now())
        logfile.write(rv + "\n")
        logfile.write(model + "\n")
        for message in messages:
            logfile.write("****** " + message["role"] + "\n")
            logfile.write(message["content"])
            logfile.write("\n")
    return rv


def call_api(messages, model:str):
    count_exceptions = 0
    while True:
        try:
            if "gpt-4" in model.lower():
                client = openai.OpenAI()
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.0,
                    timeout=240,
                    seed=42,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    max_tokens=10000
                )
                return response.choices[0].message.content
            elif "o1" == model.lower():
                client = openai.OpenAI()
                # o1 support many fewer parameters than gpt-4* models
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    timeout=240
                )
                return response.choices[0].message.content
            elif "claude" in model.lower():
                client = anthropic.Anthropic()
                response = client.messages.create(
                    model=model,
                    max_tokens=4095,
                    temperature=0,
                    top_p=1.0,
                    messages=messages
                )
                return response.content[0].text
            elif "gemini" in model.lower():
                scopes = ["https://www.googleapis.com/auth/cloud-platform",
                          "https://www.googleapis.com/auth/generative-language"]
                credentials = \
                    service_account.Credentials.from_service_account_file('GOOGLE-API-KEY-private.json',
                                                                                    scopes=scopes)
                genai.configure(credentials=credentials)
                client = genai.GenerativeModel(model_name = model,
                                                generation_config = {"temperature": 0,
                                                                     "top_k": 1})
                if len(messages) == 1:
                    chat = client.start_chat()
                elif len(messages) == 3:
                    history = [
                        {
                            "role": "user",
                            "parts": [{"text": messages[0]["content"]}],
                        },
                        {
                            "role": "model",
                            "parts": [{"text": messages[1]["content"]}]
                        }
                    ]
                    chat = client.start_chat(history=history)
                else:
                    assert False, "unsupported number of messages"

                response = chat.send_message(messages[-1]["content"])
                return response.text
            else:
                assert False, "Unsupported API"
        except Exception as e:  # Catches most exceptions; often LLM APIs have temporary hiccups
            count_exceptions += 1
            print("EXCEPTION from ", model, f", Error Type: {type(e).__name__} {e}, try number {count_exceptions}")
            if count_exceptions >= 10:
                raise  # re-throw it, since we've tried repeatedly
            else:
                time.sleep(10)  # hopefully LLM API hiccup will be resolved
