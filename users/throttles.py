from rest_framework.throttling import UserRateThrottle

class LoginRateThrottle(UserRateThrottle):
    rate = '5/min'  # max 5 login attempts per minute

class PurchaseRateThrottle(UserRateThrottle):
    rate = '10/hour'  # max 10 purchases per hour