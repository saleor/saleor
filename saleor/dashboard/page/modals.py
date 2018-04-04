from django.template.response import TemplateResponse


PROTECTED_PAGE_ERROR_MODAL_PATH = (
    'dashboard/page/modals/protected_page_error_modal.html')


def modal_protected_page(request, page):
    # Note that we are not returning an HTTP 403,
    # as it would prevent the modal from loading.
    ctx = {'page': page}
    return TemplateResponse(request, PROTECTED_PAGE_ERROR_MODAL_PATH, ctx)
