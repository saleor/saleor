import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import React from "react";
import SVG from "react-inlinesvg";

import { createHref } from "../../misc";
import { IActiveSubMenu } from "./MenuList";
import { IMenuItem } from "./menuStructure";

export interface MenuNestedProps {
  activeItem: IActiveSubMenu;
  ariaLabel: string;
  classes: Record<
    | "menuIcon"
    | "menuListItem"
    | "menuListItemActive"
    | "menuListItemText"
    | "menuListNested"
    | "menuListNestedItem"
    | "menuListNestedOpen"
    | "subheader",
    string
  >;
  closeSubMenu: ({}) => void;
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
  menuItem,
  onMenuItemClick,
  title
}) => {
  const menuItems = menuItem.children;
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
        <Typography className={classes.subheader} variant="h5">
          {title}
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
