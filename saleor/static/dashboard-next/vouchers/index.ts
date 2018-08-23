import i18n from "../i18n";

export type VoucherType =
  | "CATEGORY"
  | "PRODUCT"
  | "SHIPPING"
  | "VALUE"
  | string;

interface Voucher {
  type: VoucherType;
  discountValueType: "PERCENTAGE" | "FIXED" | string;
  discountValue: number;
  product: {
    name: string;
  } | null;
  category: {
    name: string;
  } | null;
}
export function createVoucherName(voucher: Voucher, currency: string) {
  switch (voucher.type) {
    case "CATEGORY":
      if (voucher.discountValueType === "FIXED") {
        return i18n.t(
          "{{ value }} {{ currency }} discount for {{ category }}",
          {
            category: voucher.category.name,
            currency,
            value: voucher.discountValue
          }
        );
      }
      return i18n.t("{{ value }}% discount for {{ category }}", {
        category: voucher.category.name,
        value: voucher.discountValue
      });
    case "PRODUCT":
      if (voucher.discountValueType === "FIXED") {
        return i18n.t("{{ value }} {{ currency }} discount for {{ product }}", {
          currency,
          product: voucher.product.name,
          value: voucher.discountValue
        });
      }
      return i18n.t("{{ value }}% discount for {{ product }}", {
        product: voucher.product.name,
        value: voucher.discountValue
      });
    case "SHIPPING":
      if (voucher.discountValueType === "FIXED") {
        return i18n.t("{{ value }} {{ currency }} discount for shipping", {
          currency,
          value: voucher.discountValue
        });
      }
      return i18n.t("{{ value }}% discount for shipping", {
        value: voucher.discountValue
      });
    case "VALUE":
      if (voucher.discountValueType === "FIXED") {
        return i18n.t("{{ value }} {{ currency }} discount", {
          currency,
          value: voucher.discountValue
        });
      }
      return i18n.t("{{ value }}% discount", {
        value: voucher.discountValue
      });
  }
}
