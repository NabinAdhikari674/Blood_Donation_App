# middleware/firebase_auth_middleware.py
from firebase_admin import auth
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser

class FirebaseAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the Firebase ID token from the request headers.
        authorization_header = request.META.get("HTTP_AUTHORIZATION")
        if authorization_header is not None:
            id_token = authorization_header.split(" ").pop()
        else:
            id_token = None

        if id_token:
            try:
                # Verify the ID token using Firebase Admin SDK.
                decoded_token = auth.verify_id_token(id_token)
                # Extract user information from the decoded token.
                user_id = decoded_token['uid']
                # Get or create a Django User object based on Firebase UID.
                user = User.objects.get(username=user_id)
                # Set the user in the request for authentication.
                request.user = user

            except auth.AuthError as e:
                # Handle token verification errors, e.g., token expired.
                # request.user = AnonymousUser()
                pass

        response = self.get_response(request)
        return response
