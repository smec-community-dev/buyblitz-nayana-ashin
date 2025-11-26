from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a social provider,
        but before the login is actually processed.
        """
        # If user already exists, let them login normally
        if sociallogin.is_existing:
            return

        # For new users, store their Google data in session
        if sociallogin.account.provider == 'google':
            data = sociallogin.account.extra_data
            request.session['pending_google_signup'] = True
            request.session['google_email'] = data.get('email', '')
            request.session['google_first_name'] = data.get('given_name', '')
            request.session['google_last_name'] = data.get('family_name', '')
            request.session['google_picture'] = data.get('picture', '')

            # Prevent auto-login and redirect to role selection
            raise ImmediateHttpResponse(redirect('role_selection'))

    def save_user(self, request, sociallogin, form=None):
        """
        Override to prevent automatic user creation
        """
        return None