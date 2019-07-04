import i18n from "../i18n";
import { VoucherTypeEnum } from "../types/globalTypes";

export const translateVoucherTypes = () => ({
  [VoucherTypeEnum.SHIPPING]: i18n.t("Shipment"),
  [VoucherTypeEnum.ENTIRE_ORDER]: i18n.t("Entire order"),
  [VoucherTypeEnum.SPECIFIC_PRODUCT]: i18n.t("Specific Products")
});
