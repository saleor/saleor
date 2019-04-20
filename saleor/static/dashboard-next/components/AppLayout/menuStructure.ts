import { categoryListUrl } from "../../categories/urls";
import { collectionListUrl } from "../../collections/urls";
import { customerListUrl } from "../../customers/urls";
import { saleListUrl, voucherListUrl } from "../../discounts/urls";
import i18n from "../../i18n";
import { orderDraftListUrl, orderListUrl } from "../../orders/urls";
import { productListUrl } from "../../products/urls";
import { languageListUrl } from "../../translations/urls";
import { PermissionEnum } from "../../types/globalTypes";

export interface IMenuItem {
  ariaLabel: string;
  children?: IMenuItem[];
  label: string;
  permission?: PermissionEnum;
  url?: string;
}

const menuStructure: IMenuItem[] = [
  {
    ariaLabel: "home",
    label: i18n.t("Home", { context: "Menu label" }),
    url: "/"
  },
  {
    ariaLabel: "catalogue",
    children: [
      {
        ariaLabel: "products",
        label: i18n.t("Products", { context: "Menu label" }),
        url: productListUrl()
      },
      {
        ariaLabel: "categories",
        label: i18n.t("Categories", { context: "Menu label" }),
        url: categoryListUrl()
      },
      {
        ariaLabel: "collections",
        label: i18n.t("Collections", { context: "Menu label" }),
        url: collectionListUrl()
      }
    ],
    label: i18n.t("Catalogue", { context: "Menu label" }),
    permission: PermissionEnum.MANAGE_PRODUCTS
  },
  {
    ariaLabel: "orders",
    children: [
      {
        ariaLabel: "orders",
        label: i18n.t("All Orders", { context: "Menu label" }),
        permission: PermissionEnum.MANAGE_ORDERS,
        url: orderListUrl()
      },
      {
        ariaLabel: "order drafts",
        label: i18n.t("Draft Orders", { context: "Menu label" }),
        permission: PermissionEnum.MANAGE_ORDERS,
        url: orderDraftListUrl()
      }
    ],
    label: i18n.t("Orders", { context: "Menu label" }),
    permission: PermissionEnum.MANAGE_ORDERS
  },
  {
    ariaLabel: "customers",
    label: i18n.t("Customers", { context: "Menu label" }),
    permission: PermissionEnum.MANAGE_USERS,
    url: customerListUrl()
  },

  {
    ariaLabel: "discounts",
    children: [
      {
        ariaLabel: "sales",
        label: i18n.t("Sales", { context: "Menu label" }),
        url: saleListUrl()
      },
      {
        ariaLabel: "vouchers",
        label: i18n.t("Vouchers", { context: "Menu label" }),
        url: voucherListUrl()
      }
    ],
    label: i18n.t("Discounts", { context: "Menu label" }),
    permission: PermissionEnum.MANAGE_DISCOUNTS
  },
  {
    ariaLabel: "translations",
    label: i18n.t("Translations", { context: "Menu label" }),
    permission: PermissionEnum.MANAGE_TRANSLATIONS,
    url: languageListUrl
  }
];
export default menuStructure;
