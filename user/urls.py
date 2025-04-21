from django.urls import path
from user.views import (unblock_user, 
    get_blocked_users,
    block_user, 
    check_email_auth, 
    create_user, 
    delete_user, 
    get_user_info, 
    send_purdue_verification, 
    update_user_info, 
    verify_purdue_email, 
    upload_profile_picture,
    get_history,
    addToHistory
)

urlpatterns = [
    path('create_user/', create_user, name="create_user"),
    path('info/', get_user_info, name="get_user_info"), 
    path('info/<str:uid>/', get_user_info, name="get_user_by_uid"), 
    path('update/', update_user_info, name="update_user_info"),
    path('delete_user/', delete_user, name="delete_user"),
    path('send_purdue_verification/', send_purdue_verification, name="send_purdue_verification"),
    path('verify_purdue_email/', verify_purdue_email, name="verify_purdue_email"),
    path('check_email_auth', check_email_auth, name="check_email_auth"),
    path('upload_profile_picture/', upload_profile_picture, name="upload_profile_picture"),
    path('blockUser/<str:uid>/', block_user, name="block_user"),
    path('unblockUser/<str:uid>/', unblock_user, name="unblock_user"),
    path('getBlockedUsers/', get_blocked_users, name="get_blocked_users"),
    path('getHistory/<str:uid>/', get_history, name="get_history"),
    path('addToHistory/', addToHistory, name="get_history")
]
