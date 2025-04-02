from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.redirect_to_home_or_login, name='redirect'),
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logoutUser, name='logout'),
    path('home/', views.home, name='home'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('booking/', views.booking_view, name='booking'),
    path("my-appointments/", views.my_appointments, name="my_appointments"),
    path("cancel-booking/<int:booking_id>/", views.cancel_booking, name="cancel_booking"),
    path("report/<int:booking_id>/", views.report_view, name="report"),
    path('cnc/', views.cnc, name='cnc'),
    path('3d_printing/', views.printing, name='3d_printing'),
    path('reach_limit/', views.reach_limit_page, name='reach_limit'),
    
    # Password Reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name="password_reset/password_reset.html"), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name="password_reset/password_reset_done.html"), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="password_reset/password_reset_confirm.html"), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name="password_reset/password_reset_complete.html"), name='password_reset_complete'),

]
