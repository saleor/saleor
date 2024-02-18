from ..mutations.utils import apply_gift_reward_if_applicable_on_checkout_creation


def test_apply_gift_reward_if_applicable(
    checkout_with_item, gift_promotion_rule, order_promotion_rule, promotion_rule
):
    # given
    checkout = checkout_with_item
    lines_count = checkout.lines.count()

    # when
    apply_gift_reward_if_applicable_on_checkout_creation(checkout)

    # then
    checkout.refresh_from_db()
    assert checkout.lines.count() == lines_count + 1
    gift_line = checkout.lines.filter(is_gift=True).first()
    assert gift_line
    assert gift_line.discounts.count() == 1


def test_apply_gift_reward_if_applicable_no_gift_promotion_rules(
    checkout_with_item, order_promotion_rule, promotion_rule
):
    # given
    checkout = checkout_with_item
    lines_count = checkout.lines.count()

    # when
    apply_gift_reward_if_applicable_on_checkout_creation(checkout)

    # then
    checkout.refresh_from_db()
    assert checkout.lines.count() == lines_count


def test_apply_gift_reward_if_applicable_no_gift_promotion_rules_for_checkout_channel(
    checkout_with_item, gift_promotion_rule, order_promotion_rule, promotion_rule
):
    # given
    checkout = checkout_with_item
    lines_count = checkout.lines.count()
    gift_promotion_rule.channels.remove(checkout.channel)

    # when
    apply_gift_reward_if_applicable_on_checkout_creation(checkout)

    # then
    checkout.refresh_from_db()
    assert checkout.lines.count() == lines_count
