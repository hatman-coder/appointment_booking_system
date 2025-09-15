from django.utils.deprecation import MiddlewareMixin


class PrintIpAddressMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        ip_address = request.META.get('REMOTE_ADDR')
        print(f'IP Address: {ip_address}')
