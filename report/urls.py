
from django.urls import path
from report.views import (
    get_all_reports,
    get_reports_about_user,
    get_reports_by_user,
    create_report,
    delete_report,
    ban_user,
)

urlpatterns = [
    path('get/', get_all_reports, name="get_all_reports"),
    path('about/<str:uid>/', get_reports_about_user, name="get_reports_about_user"),
    path('by/<str:uid>/', get_reports_by_user, name="get_reports_by_user"),
    path('create/', create_report, name="create_report"),
    path('delete/<int:report_id>/', delete_report, name='delete_report'),
    path('ban/<str:uid>/', ban_user, name='ban_user'),
]
