from phonenumbers.phonenumberutil import country_code_for_region

from .i18n import AddressMetaForm, get_address_form_class


def get_address_form(
    data, country_code, initial=None, instance=None, enable_normalization=True, **kwargs
):
    """返回一个给定国家/地区的地址表单。

    Args:
        data (dict): 表单数据。
        country_code (str): 国家的 ISO 3166-1 alpha-2 代码。
        initial (dict, optional): 表单的初始数据。默认为 None。
        instance (Address, optional): 要绑定的地址模型实例。默认为 None。
        enable_normalization (bool, optional): 是否启用地址标准化。默认为 True。
        **kwargs: 传递给表单类的其他关键字参数。

    Returns:
        Form: 一个地址表单实例。
    """
    country_form = AddressMetaForm(data, initial=initial)
    if country_form.is_valid():
        country_code = country_form.cleaned_data["country"]

    if initial is None and country_code:
        initial = {}
    if country_code:
        initial["phone"] = f"+{country_code_for_region(country_code)}"
    address_form_class = get_address_form_class(country_code)

    if instance is not None:
        address_form = address_form_class(
            data, instance=instance, enable_normalization=enable_normalization, **kwargs
        )
    else:
        initial_address = initial
        address_form = address_form_class(
            data or None,
            initial=initial_address,
            enable_normalization=enable_normalization,
            **kwargs,
        )

    if hasattr(address_form.fields["country_area"], "choices"):
        choices = address_form.fields["country_area"].choices
        choices = [(choice[1], choice[1]) for choice in choices]
        address_form.fields["country_area"].choices = choices
    return address_form
