import * as React from "react";
import Navigator from "../components/Navigator";

import { UserContext } from "../auth";
import i18n from "../i18n";
import AccountCircle from "../icons/AccountCircle";
import Ballot from "../icons/Ballot";
import Folder from "../icons/Folder";
import LocalShipping from "../icons/LocalShipping";
import Monetization from "../icons/Monetization";
import Navigation from "../icons/Navigation";
import Pages from "../icons/Pages";
import StoreMall from "../icons/StoreMall";
import { productTypeListUrl } from "../productTypes";
import { staffListUrl } from "../staff";
import ConfigurationPage, { MenuItem } from "./ConfigurationPage";

export const configurationMenu: MenuItem[] = [
  {
    description: i18n.t("Define types of products you sell"),
    icon: <Folder fontSize="inherit" />,
    permission: "product.manage_products",
    title: i18n.t("Product Types"),
    url: productTypeListUrl
  },
  {
    description: i18n.t("Define attributes of products yousell"),
    icon: <Ballot fontSize="inherit" />,
    permission: "product.manage_products",
    title: i18n.t("Attributes")
  },
  {
    description: i18n.t("Manage your employees and their permissions"),
    icon: <AccountCircle fontSize="inherit" />,
    permission: "account.manage_staff",
    title: i18n.t("Staff Members"),
    url: staffListUrl
  },
  {
    description: i18n.t("Manage how you ship out orders."),
    icon: <LocalShipping fontSize="inherit" />,
    permission: "shipping.manage_shipping",
    title: i18n.t("Shipping Methods")
  },
  {
    description: i18n.t("Manage how your store charges tax"),
    icon: <Monetization fontSize="inherit" />,
    permission: "product.manage_products",
    title: i18n.t("Taxes")
  },
  {
    description: i18n.t("Define how users can navigate through your store"),
    icon: <Navigation fontSize="inherit" />,
    permission: "menu.manage_menus",
    title: i18n.t("Navigation")
  },
  {
    description: i18n.t("View and update your site settings"),
    icon: <StoreMall fontSize="inherit" />,
    permission: "site.manage_settings",
    title: i18n.t("Site Settings")
  },
  {
    description: i18n.t("Manage and add additional pages"),
    icon: <Pages fontSize="inherit" />,
    permission: "page.manage_pages",
    title: i18n.t("Pages")
  }
];

export const configurationMenuUrl = "/configuration/";

export const ConfigurationSection: React.StatelessComponent = () => (
  <UserContext.Consumer>
    {({ user }) => (
      <Navigator>
        {navigate => (
          <ConfigurationPage
            menu={configurationMenu}
            user={user}
            onSectionClick={navigate}
          />
        )}
      </Navigator>
    )}
  </UserContext.Consumer>
);
export default ConfigurationSection;
