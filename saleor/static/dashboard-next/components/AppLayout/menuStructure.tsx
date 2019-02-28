import MoneyIcon from "@material-ui/icons/MoneyOutlined";
import PersonOutline from "@material-ui/icons/PersonOutline";
import * as React from "react";

import { categoryListUrl } from "../../categories/urls";
import { collectionListUrl } from "../../collections/urls";
import { customerListUrl } from "../../customers/urls";
import { saleListUrl, voucherListUrl } from "../../discounts/urls";
import i18n from "../../i18n";
import Home from "../../icons/Home";
import Shop from "../../icons/Shop";
import Truck from "../../icons/Truck";
import { orderListUrl } from "../../orders/urls";
import { productListUrl } from "../../products/urls";
import { PermissionEnum } from "../../types/globalTypes";

export interface IMenuItem {
  ariaLabel: string;
  children?: IMenuItem[];
  icon: React.ReactNode;
  label: string;
  permission?: PermissionEnum;
  url?: string;
}

const menuStructure: IMenuItem[] = [
  {
    ariaLabel: "home",
    icon: <Home />,
    label: i18n.t("Home", { context: "Menu label" }),
    url: "/"
  },
  {
    ariaLabel: "catalogue",
    children: [
      {
        ariaLabel: "products",
        icon: <Shop />,
        label: i18n.t("Products", { context: "Menu label" }),
        url: productListUrl()
      },
      {
        ariaLabel: "categories",
        icon: <Shop />,
        label: i18n.t("Categories", { context: "Menu label" }),
        url: categoryListUrl
      },
      {
        ariaLabel: "collections",
        icon: <Shop />,
        label: i18n.t("Collections", { context: "Menu label" }),
        url: collectionListUrl
      }
    ],
    icon: <Shop />,
    label: i18n.t("Catalogue", { context: "Menu label" }),
    permission: PermissionEnum.MANAGE_PRODUCTS
  },
  {
    ariaLabel: "orders",
    icon: <Truck />,
    label: i18n.t("Orders", { context: "Menu label" }),
    permission: PermissionEnum.MANAGE_ORDERS,
    url: orderListUrl()
  },
  {
    ariaLabel: "customers",
    icon: <PersonOutline />,
    label: i18n.t("Customers", { context: "Menu label" }),
    permission: PermissionEnum.MANAGE_USERS,
    url: customerListUrl
  },
  {
    ariaLabel: "discounts",
    children: [
      {
        ariaLabel: "sales",
        icon: <MoneyIcon />,
        label: i18n.t("Sales", { context: "Menu label" }),
        url: saleListUrl
      },
      {
        ariaLabel: "vouchers",
        icon: <MoneyIcon />,
        label: i18n.t("Vouchers", { context: "Menu label" }),
        url: voucherListUrl
      }
    ],
    icon: <MoneyIcon />,
    label: i18n.t("Discounts", { context: "Menu label" }),
    permission: PermissionEnum.MANAGE_DISCOUNTS
  }
];
export default menuStructure;
