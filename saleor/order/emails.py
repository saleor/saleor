from templated_email import send_templated_mail


CONFIRMATION_TEMPLATE = 'foo'


def send_confirmation(address):
    send_templated_mail(from_email=address, recipient_list=[], context={},
                        template_name=CONFIRMATION_TEMPLATE)
