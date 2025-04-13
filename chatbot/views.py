import os
import json
import logging
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI, APIError, Timeout
from .models import ChatHistory
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

# API Configuration
LLAMA_API_KEY = "c4a6dcee-bdab-4825-a18a-313345156360"
OPEN_ROUTER_API_KEY = "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"

# Define model API mapping
MODEL_API_MAP = {
    "llama": {
        "api_key": LLAMA_API_KEY,
        "base_url": "https://api.llama-api.com",
        "model": "llama3.3-70b"
    },
    "deepseek": {
        "api_key": LLAMA_API_KEY,
        "base_url": "https://api.llama-api.com",
        "model": "deepseek-r1"
    },
    "mistralai": {
        "api_key": LLAMA_API_KEY,
        "base_url": "https://api.llama-api.com",
        "model": "mistral-7b-instruct"
    },
    "qwen": {
        "api_key": LLAMA_API_KEY,
        "base_url": "https://api.llama-api.com",
        "model": "Qwen2.5-7B"
    },
    "gemini": {
        "api_key": LLAMA_API_KEY,
        "base_url": "https://api.llama-api.com",
        "model": "gemma3-12b"
    },
    "gemini_pro": {
        "api_key": LLAMA_API_KEY,
        "base_url": "https://api.llama-api.com",
        "model": "gemma3-27b"
    }
}


@csrf_exempt
def precheck_view(request):
    if request.method == 'POST':
        # Extract the user's input from the request
        data = json.loads(request.body)
        user_input = data.get('prompt', '').strip()

        print("User prompt: ", user_input)

        # Initialize the OpenAI client
        client = OpenAI(api_key=LLAMA_API_KEY, base_url="https://api.llama-api.com")

        # Define the prompt for the LLM
        prompt = (
            "Check if the following question is related to finance, banking, Islamic finance, investment, stocks, or startups. "
            "Return only 'yes' or 'no' as the answer. Do not provide any extra information or explanation.\n\n"
            "Examples:\n"
            "1. Question: What is the difference between conventional and Islamic banking?\n"
            "   Answer: yes\n"
            "2. Question: How do I bake a chocolate cake?\n"
            "   Answer: no\n"
            "3. Question: What are the best practices for pitching a startup to investors?\n"
            "   Answer: yes\n"
            "4. Question: How do I calculate the return on investment for a stock?\n"
            "   Answer: yes\n"
            "5. Question: What is the capital of France?\n"
            "   Answer: no\n\n"
            f"Question: {user_input}\n"
            "Answer:"
        )

        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3.3-70b",
                stream=False,
                timeout=60  # Enforcing a 60-second timeout
            )

            llm_response = chat_completion.choices[0].message.content


            print("llm_response: ", llm_response)

            # Determine if the response is 'yes' or 'no'
            # allowed = "yes" if llm_response == "yes" else "no"
            allowed = "yes"

            # Return the result as a JSON response
            return JsonResponse({"allowed": allowed})

        except Exception as e:
            # Handle any errors that occur during the LLM call
            return JsonResponse({"error": str(e)}, status=500)

    else:
        # Return an error if the request method is not POST
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
    

@csrf_exempt
def chat_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        # Parse JSON request body
        data = json.loads(request.body)
        query = data.get("query")
        model_name = data.get("model")

        if not query or not model_name:
            return JsonResponse({"error": "Missing query or model"}, status=400)

        # Validate model selection
        if model_name not in MODEL_API_MAP:
            return JsonResponse({"error": "Invalid model selected"}, status=400)

        # Get model API configuration
        api_config = MODEL_API_MAP[model_name]
        llm_version = api_config["model"]

        try:
            # print(f"Sending chat request to {model_name}...")  # Debugging

            # Initialize OpenAI Client
            client = OpenAI(api_key=api_config["api_key"], base_url=api_config["base_url"])

            # Send request with timeout
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": f"Respond in HTML format: {query}"}],
                model=api_config["model"],
                stream=False,
                timeout=60  # Enforcing a 60-second timeout
            )

            response_text = chat_completion.choices[0].message.content
            # print(f"Response from {model_name}: {response_text}")  # Debugging

        except Timeout:
            response_text = "Request timed out."
            print(f"Timeout error for {model_name}")  # Debugging
        except APIError as e:
            response_text = f"API error: {str(e)}"
            print(f"API error for {model_name}: {str(e)}")  # Debugging
        except Exception as e:
            response_text = f"Unexpected error: {str(e)}"
            print(f"Unexpected error for {model_name}: {str(e)}")  # Debugging

        # Store response in session memory
        if "chat_responses" not in request.session:
            request.session["chat_responses"] = {}

        request.session["prompt"] = query
        request.session["chat_responses"][model_name] = response_text
        request.session.modified = True  # Ensure session is saved

        return JsonResponse({"model": model_name, "llm_version": llm_version, "response": response_text})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected server error: {str(e)}"}, status=500)



@csrf_exempt
def summary_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        # Parse JSON request body
        data = json.loads(request.body)
        selected_models = data.get("models", [])
        selected_responses = data.get("texts", [])
        print(selected_responses)

        # print("Selected models:", selected_models)  # Debugging

        if not selected_models:
            return JsonResponse({"error": "No models selected"}, status=400)
        
        single_model = request.GET.get('single_model', False)  # Returns 'true' or None
        prompt = request.session.get("prompt", "")

        # Retrieve stored responses from session
        chat_responses = request.session.get("chat_responses", {})

        # Validate that all selected models have stored responses
        missing_models = [model for model in selected_models if model not in chat_responses]
        if missing_models:
            return JsonResponse({"error": f"No stored response for models: {', '.join(missing_models)}"}, status=400)

        # Combine responses into a single input for summarization
        combined_input = "\n\n".join(
            [f"{model}: {chat_responses[model]}" for model in selected_responses]
        )

        summaries = {}

        for model_name in selected_models:
            if model_name not in MODEL_API_MAP:
                return JsonResponse({"error": f"Invalid model: {model_name}"}, status=400)

            # Get model API configuration
            api_config = MODEL_API_MAP[model_name]
            llm_version = api_config["model"]

            try:
                print(f"Sending summary request to {model_name}...")  # Debugging

                # Initialize OpenAI Client
                client = OpenAI(api_key=api_config["api_key"], base_url=api_config["base_url"])

                # Send request to generate summary
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": (
                            "You are an expert analyst summarizing multiple reports on {prompt}. Each report covers overlapping but potentially unique insights. "
                            "Your task is to synthesize them into a concise, non-redundant summary that includes all key information. "
                            "Consider applying the Mutually Exclusive Collectively Exhaustive (MECE) approach when combining and summarizing. "
                            "Please review the following summaries based on user selection and merge similar points into unified explanations. "
                            "Organize the summary into clear sections by themes, highlight unique insights separately, and use bullet points, paragraphs, or tables for clarity. "
                            "Maintain a formal, informative, and detailed tone. This prompt is intended for internal processing to ensure thorough and complete responses."
                        )},
                        {"role": "user", "content": f"Summarize the following in HTML format: {combined_input}"}
                    ],
                    model=api_config["model"],
                    stream=False,
                    timeout=60  # Set timeout to prevent hanging
                )

                summary_text = chat_completion.choices[0].message.content
                # print(f"Summary from {model_name}: {summary_text}")  # Debugging

                # Store summary in session memory
                if "summary_responses" not in request.session:
                    request.session["summary_responses"] = {}

                request.session["summary_responses"][model_name] = summary_text
                request.session.modified = True  # Ensure session is saved

                # Store summary in response dictionary
                summaries[model_name] = summary_text

                if single_model:
                    # Check if the user already has 5 entries
                    chat_count = ChatHistory.objects.filter(user=request.user).count()
                    if chat_count >= 5:
                        oldest_chat = ChatHistory.objects.filter(user=request.user).order_by('created_at').first()
                        oldest_chat.delete()  # Delete the oldest chat

                    # Save the new chat history
                    ChatHistory.objects.create(
                        user=request.user,
                        prompt=prompt,
                        response=summary_text
                    )
                    # print("Last Summary: ", request.session['chat_responses'])
                    # Remove all session data after saving
                    del request.session["prompt"]
                    del request.session["summary_responses"]

                    initial_response = request.session['chat_responses'][model_name]

                    return JsonResponse({"summaries": summaries, "llm_version": llm_version, "initial_response": initial_response})

            except Timeout:
                summaries[model_name] = "Request timed out."
                print(f"Timeout error for {model_name}")  # Debugging
            except APIError as e:
                summaries[model_name] = f"API error: {str(e)}"
                print(f"API error for {model_name}: {str(e)}")  # Debugging
            except Exception as e:
                summaries[model_name] = f"Unexpected error: {str(e)}"
                print(f"Unexpected error for {model_name}: {str(e)}")  # Debugging

        # print("Final summaries:", summaries)  # Debugging

        return JsonResponse({"summaries": summaries, "llm_version": llm_version})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Unexpected server error: {str(e)}"}, status=500)


@login_required
def chat_detail(request, chat_id):
    chat = get_object_or_404(ChatHistory, id=chat_id)
    context = {
        'chat': chat
    }
    return render(request, 'chats/chat_detail.html', context)


@csrf_exempt
def fetch_chat_history(request):
    user = request.user  # Current logged-in user
    
    chats = ChatHistory.objects.filter(user=user).order_by('-created_at')[:5]
    chat_list = [
        {"id": chat.id, "prompt": chat.prompt[:50]} for chat in chats
    ]
    return JsonResponse({"chat_history": chat_list})



def send_review(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            model_name = data.get("model", "Unknown Model")
            review_text = data.get("review", "")

            if not review_text.strip():
                return JsonResponse({"error": "Review cannot be empty!"}, status=400)

            subject = f"New Review for {model_name}"
            email_body = f"A new review has been submitted for {model_name}:\n\n\n{review_text}"

            send_mail(
                subject,
                email_body,
                f'Islamic Analytix <{settings.DEFAULT_FROM_EMAIL}>',  # Sender email from settings
                ["islamicanalytics5@gmail.com"],  # Replace with your recipient email
                fail_silently=False,
            )

            return JsonResponse({"message": "Review submitted successfully!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)