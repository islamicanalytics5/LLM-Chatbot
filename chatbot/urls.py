from django.urls import path
from .views import chat_view, summary_view, fetch_chat_history, chat_detail, precheck_view, send_review

urlpatterns = [
    # path('response/', chatbot_response, name='chatbot_response'),
    path('summarize/', summary_view, name='chatbot_summary'),
    path('test/', chat_view, name="test-chat"),
    path("chat/", chat_view, name="chat_url"),
    path('chat-detail/<int:chat_id>/', chat_detail, name='chat_detail'),
    path('fetch-chat-history/', fetch_chat_history, name='fetch_chat_history'),
    path('precheck/', precheck_view, name="precheck"),
    path("send-review/", send_review, name="send_review"),
]

