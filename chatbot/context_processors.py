from .models import ChatHistory

def chat_history_processor(request):
    if request.user.is_authenticated:
        chat_history = ChatHistory.objects.filter(user=request.user).order_by('-created_at')[:5]
    else:
        chat_history = []
    return {'chat_history_menu': chat_history}