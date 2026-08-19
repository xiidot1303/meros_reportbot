from django.urls import path, re_path
from django.contrib.auth.views import (
    LoginView, 
    LogoutView, 
    PasswordChangeDoneView, 
    PasswordChangeView
)

from app.views import (
    main
)
from app.views.payment import PaymentReceiveView
from app.views.transport import OrderTransportView
from app.views.docs import (
    DocsLoginView, DocsLogoutView, OpenAPISchemaView, StoplightDocsView, SwaggerUIView
)

urlpatterns = [
    path('', main.main),
    # login
    path('accounts/login/', LoginView.as_view()),
    path('changepassword/', PasswordChangeView.as_view(
        template_name = 'registration/change_password.html'), name='editpassword'),
    path('changepassword/done/', PasswordChangeDoneView.as_view(
        template_name = 'registration/afterchanging.html'), name='password_change_done'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # payments API
    path('api/payments/', PaymentReceiveView.as_view()),
    path('api/order-transport/', OrderTransportView.as_view()),

    # API documentation (separate login from the admin)
    path('api/login/', DocsLoginView.as_view(), name='api-docs-login'),
    path('api/logout/', DocsLogoutView.as_view(), name='api-docs-logout'),
    path('api/schema/', OpenAPISchemaView.as_view(), name='openapi-schema'),
    path('api/docs/', SwaggerUIView.as_view(), name='api-docs'),
    path('api/reference/', StoplightDocsView.as_view(), name='api-reference'),

    # files
    re_path(r'^files/(?P<path>.*)$', main.get_file),


]
