import i18n from "@saleor/i18n";

export function translateBoolean(value: boolean): string {
  return value ? i18n.t("Yes") : i18n.t("No");
}
