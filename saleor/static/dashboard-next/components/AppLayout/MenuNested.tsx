import Hidden from "@material-ui/core/Hidden";
import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import React from "react";
import SVG from "react-inlinesvg";

import useTheme from "@saleor/hooks/useTheme";
import { createHref } from "../../misc";
import { IActiveSubMenu } from "./MenuList";
import { IMenuItem } from "./menuStructure";

import menuArrowIcon from "../../../images/menu-arrow-icon.svg";

export interface MenuNestedProps {
  activeItem: IActiveSubMenu;
  ariaLabel: string;
  classes: Record<
    | "menuIcon"
    | "menuListItem"
    | "menuListItemActive"
    | "menuListItemText"
    | "menuListNested"
    | "menuListNestedClose"
    | "menuListNestedCloseDark"
    | "menuListNestedIcon"
    | "menuListNestedIconDark"
    | "menuListNestedItem"
    | "menuListNestedOpen"
    | "subHeader"
    | "subHeaderDark"
    | "subHeaderTitle",
    string
  >;
  closeSubMenu: ({}) => void;
  icon: string;
  menuItem: IMenuItem;
  title: string;
  handleSubMenu: (itemLabel: string) => void;
  onMenuItemClick: (url: string, event: React.MouseEvent<any>) => void;
}

const MenuNested: React.FC<MenuNestedProps> = ({
  activeItem,
  ariaLabel,
  classes,
  closeSubMenu,
  icon,
  menuItem,
  onMenuItemClick,
  title
}) => {
  const menuItems = menuItem.children;
  const { isDark } = useTheme();
  const closeMenu = (menuItemUrl, event) => {
    onMenuItemClick(menuItemUrl, event);
    closeSubMenu({
      isActive: false,
      label: ""
    });
    event.stopPropagation();
    event.preventDefault();
  };
  return (
    <>
      <div
        className={classNames(classes.menuListNested, {
          [classes.menuListNestedOpen]:
            activeItem.label === ariaLabel && activeItem.isActive
        })}
      >
        <Typography
          className={classNames(classes.subHeader, {
            [classes.subHeaderDark]: isDark
          })}
          variant="h5"
        >
          <Hidden mdUp>
            <SVG
              className={classNames(classes.menuListNestedIcon, {
                [classes.menuListNestedIconDark]: isDark
              })}
              src={icon}
            />
          </Hidden>
          <div className={classes.subHeaderTitle}>{title}</div>
          <Hidden mdUp>
            <div
              className={classNames(classes.menuListNestedClose, {
                [classes.menuListNestedCloseDark]: isDark
              })}
              onClick={() =>
                closeSubMenu({
                  isActive: false,
                  label: ""
                })
              }
            >
              <SVG src={menuArrowIcon} />
            </div>
          </Hidden>
        </Typography>
        {menuItems.map(item => {
          return (
            <a
              className={classNames(classes.menuListNestedItem)}
              href={createHref(item.url)}
              onClick={event => closeMenu(item.url, event)}
              key={item.label}
            >
              <SVG className={classes.menuIcon} src={item.icon} />
              <Typography aria-label={item.ariaLabel}>{item.label}</Typography>
            </a>
          );
        })}
      </div>
    </>
  );
};
export default MenuNested;
