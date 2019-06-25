import i18n from "../i18n";
import { VoucherType } from "../types/globalTypes";

export const translateVoucherTypes = () => ({
  [VoucherType.CATEGORY]: i18n.t("Selected Categories"),
  [VoucherType.COLLECTION]: i18n.t("Selected Collections"),
  [VoucherType.PRODUCT]: i18n.t("Selected Products"),
  [VoucherType.SHIPPING]: i18n.t("Shipment"),
  [VoucherType.ENTIRE_ORDER]: i18n.t("Entire order")
});
