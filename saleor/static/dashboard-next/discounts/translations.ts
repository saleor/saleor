import i18n from "../i18n";
import { VoucherType } from "../types/globalTypes";

export const translateVoucherTypes = () => ({
  [VoucherType.SHIPPING]: i18n.t("Shipment"),
  [VoucherType.ENTIRE_ORDER]: i18n.t("Entire order"),
  [VoucherType.SPECIFIC_PRODUCT]: i18n.t("Specific Products")
});
