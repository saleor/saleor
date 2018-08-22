import * as React from "react";
import Navigator from "../components/Navigator";

import i18n from "../i18n";
import AccountCircle from "../icons/AccountCircle";
import Ballot from "../icons/Ballot";
import Folder from "../icons/Folder";
import LocalShipping from "../icons/LocalShipping";
import Monetization from "../icons/Monetization";
import Navigation from "../icons/Navigation";
import Pages from "../icons/Pages";
import StoreMall from "../icons/StoreMall";
import ConfigurationPage from "./ConfigurationPage";

export const configurationMenu = [
  {
    description: i18n.t("Define types of products you sell"),
    disabled: true,
    icon: Folder,
    title: i18n.t("Product Types"),
    url: "/product/"
  },
  {
    description: i18n.t("Define attributes of products yousell"),
    disabled: true,
    icon: Ballot,
    title: i18n.t("Attributes"),
    url: "/attributes/"
  },
  {
    description: i18n.t("Manage your employees and their permissions"),
    disabled: true,
    icon: AccountCircle,
    title: i18n.t("Staff Members"),
    url: "/staff/"
  },
  {
    description: i18n.t("Manage how you ship out orders."),
    disabled: true,
    icon: LocalShipping,
    title: i18n.t("Shipping Methods"),
    url: "/shipping/"
  },
  {
    description: i18n.t("Manage how your store charges tax"),
    disabled: true,
    icon: Monetization,
    title: i18n.t("Taxes"),
    url: "/taxes/"
  },
  {
    description: i18n.t("Define how users can navigate through your store"),
    disabled: true,
    icon: Navigation,
    title: i18n.t("Navigation"),
    url: "/navigation/"
  },
  {
    description: i18n.t("View and update your site settings"),
    disabled: true,
    icon: StoreMall,
    title: i18n.t("Site Settings"),
    url: "/settings/"
  },
  {
    description: i18n.t("Manage and add additional pages"),
    disabled: false,
    icon: Pages,
    title: i18n.t("Pages"),
    url: "/pages/"
  }
];

export const ConfigurationSection: React.StatelessComponent = () => (
  <Navigator>
    {navigate => (
      <ConfigurationPage menu={configurationMenu} onSectionClick={navigate} />
    )}
  </Navigator>
);
export default ConfigurationSection;
