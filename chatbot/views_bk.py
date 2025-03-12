from django.http import HttpResponse, JsonResponse
import time
import json
from django.middleware.csrf import get_token
from django.urls import reverse

# import os
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# import json
# from langchain.chat_models import init_chat_model
# from langchain_core.messages import HumanMessage, AIMessage
# from langchain.memory import ConversationBufferMemory







def test_chat_view(request):
    # Set Mistral API Key
    os.environ["OPENAI_API_KEY"] = MISTRAL_API_KEY  # Replace with actual API Key

    # Initialize Mistral Model
    model = init_chat_model(
        "mistral-large-latest",
        model_provider="openai",  # Mistral uses OpenAI-style API
        openai_api_base="https://api.mistral.ai/v1"  # Mistral API Base URL
    )

    # Invoke Model with a Test Message
    response = model.invoke([HumanMessage(content="Hello, world!")])

    return JsonResponse({"response": response.content})  # Return JSON response


def chatbot_response(request):
    if request.method == "POST":
        query = request.POST.get("query", "")
        models = request.POST.getlist("models")

        if not models:
            return HttpResponse("")
        

        # Get the first model
        model = models.pop(0)

        # Simulate processing delay
        time.sleep(1)

        # Dummy response
        dummy_response = f"<p class='new-message fade-in'><strong>{model.capitalize()}:</strong><br>This is a response for '{query}'.</p>"

        if 'responses' not in request.session:
            request.session['responses'] = []
            print("Initializing session responses.")  # Debugging

        # Append the response to the session
        request.session['responses'].append(dummy_response)

        # Save session to ensure changes are reflected
        request.session.modified = True


        # Get CSRF token
        csrf_token = get_token(request)

        summary_url = reverse('chatbot_summary')

        # If more models exist, trigger the next request
        if models:
            next_request_script = f"""
                <script>
                    setTimeout(function() {{
                        let chatMessages = document.getElementById("chatMessages");

                        // Show loader before sending the next request
                        let loader = document.createElement("p");
                        loader.classList.add("loader-message", "fade-in");
                        loader.innerHTML = `<strong>Bot:</strong> Processing...`;
                        loader.setAttribute("id", "loading-message"); // Add an ID for easy removal
                        chatMessages.appendChild(loader);

                        htmx.ajax('POST', '{request.path}', {{
                            target: '#chatMessages',
                            swap: 'beforeend',
                            values: {{ query: '{query}', models: {json.dumps(models)} }},
                            headers: {{ 'X-CSRFToken': '{csrf_token}' }}
                        }}).then(function(response) {{
                            // Wait for HTMX to process, then remove the loader
                            let existingLoader = document.getElementById("loading-message");
                            if (existingLoader) existingLoader.remove();

                            // Scroll to the bottom
                            chatMessages.scrollTop = chatMessages.scrollHeight - chatMessages.clientHeight;
                        }});
                    }}, 500);
                </script>
            """
        else:
            next_request_script = f"""
                <script>
                    setTimeout(function() {{
                        let chatMessages = document.getElementById("chatMessages");

                        // Show loader before sending the next request
                        let loader = document.createElement("p");
                        loader.classList.add("loader-message", "fade-in");
                        loader.innerHTML = `<strong>Bot:</strong> Generating summary...`;
                        loader.setAttribute("id", "loading-message"); // Add an ID for easy removal
                        chatMessages.appendChild(loader);

                        htmx.ajax('POST', '{summary_url}', {{
                            target: '#chatMessages',
                            swap: 'beforeend',
                            values: {{ query: '{query}', models: {json.dumps(models)} }},
                            headers: {{ 'X-CSRFToken': '{csrf_token}' }}
                        }}).then(function(response) {{
                            // Wait for HTMX to process, then remove the loader
                            let existingLoader = document.getElementById("loading-message");
                            if (existingLoader) existingLoader.remove();

                            // Scroll to the bottom
                            chatMessages.scrollTop = chatMessages.scrollHeight - chatMessages.clientHeight;
                        }});
                    }}, 500);
                </script>
            """
        

        return HttpResponse(dummy_response + next_request_script)

    return HttpResponse("")


from django.http import HttpResponse, JsonResponse


def summary_response(request):
    if request.method == "POST":
        # Check if the session contains responses
        if 'responses' not in request.session:
            return JsonResponse({"error": "No responses in session"}, status=400)

        final_responses = request.session['responses']

        # Create the summary
        summary = "<p class='new-message fade-in'><strong>Summary:</strong><br>All models processed successfully.</p>"

        # Combine all responses with the summary
        final_response = ''.join(final_responses) + summary

        # Debugging: print final responses before returning the summary
        print("Final responses:", final_responses)

        # Clear session memory after returning the final response
        del request.session['responses']

        # Return the final response
        return HttpResponse(final_response)

    return JsonResponse({"error": "Invalid request"}, status=400)



