def test_checkout_line_info_repr(checkout_lines_info):
    line_info = checkout_lines_info[0]
    line_repr = repr(line_info)

    discounts_listed = (
        [discount.id for discount in line_info.discounts] if line_info.discounts else []
    )

    assert f"line_id={line_info.line.id}" in line_repr
    assert f"product_name={line_info.product.name}" in line_repr
    assert f"variant={line_info.variant}" in line_repr
    assert f"quantity={line_info.line.quantity}" in line_repr
    assert f"discount={discounts_listed}" in line_repr


def test_checkout_info_repr(checkout_info):
    checkout_repr = repr(checkout_info)

    line_ids = [line.line.id for line in checkout_info.lines]
    discounts_listed = (
        [discount.id for discount in checkout_info.discounts]
        if checkout_info.discounts
        else []
    )

    assert f"token={checkout_info.checkout.token}" in checkout_repr
    assert (
        f"user_id={checkout_info.user.id if checkout_info.user else None}"
        in checkout_repr
    )
    assert f"channel_slug={checkout_info.channel.slug}" in checkout_repr
    assert f"discounts={discounts_listed}" in checkout_repr
    assert f"line_ids={line_ids}" in checkout_repr
