import Hidden from "@material-ui/core/Hidden";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import React from "react";
import SVG from "react-inlinesvg";

import useTheme from "@saleor/hooks/useTheme";
import menuArrowIcon from "../../../images/menu-arrow-icon.svg";
import { createHref } from "../../misc";
import { drawerWidthExpanded } from "./consts";
import { IActiveSubMenu } from "./MenuList";
import { IMenuItem } from "./menuStructure";

const styles = (theme: Theme) =>
  createStyles({
    menuIcon: {
      "& svg": {
        height: 32,
        width: 32
      },
      display: "inline-block",
      position: "relative",
      top: 8
    },
    menuListNested: {
      background: theme.palette.background.paper,
      height: "100vh",
      position: "absolute",
      right: 0,
      top: 0,
      transition: `right  ${theme.transitions.duration.shorter}ms ease`,
      width: 300,
      zIndex: -1
    },
    menuListNestedClose: {
      "& svg": {
        fill: theme.palette.primary.main,
        left: 7,
        position: "relative",
        top: -2
      },
      border: `solid 1px #EAEAEA`,
      borderRadius: "100%",
      cursor: "pointer",
      height: 32,
      position: "absolute",
      right: 32,
      top: 35,
      transform: "rotate(180deg)",
      width: 32
    },
    menuListNestedCloseDark: {
      border: `solid 1px #252728`
    },
    menuListNestedHide: {
      opacity: 0
    },
    menuListNestedIcon: {
      "& path": {
        fill: "initial"
      },
      "& svg": { height: 32, position: "relative", top: 7, width: 32 }
    },
    menuListNestedIconDark: {
      "& path": {
        fill: theme.palette.common.white
      }
    },
    menuListNestedItem: {
      "&:hover": {
        "& p": {
          color: theme.palette.primary.main
        }
      },
      display: "block",
      padding: "0px 30px",
      textDecoration: "none"
    },
    menuListNestedOpen: {
      [theme.breakpoints.down("sm")]: {
        right: 0,
        width: drawerWidthExpanded,
        zIndex: 2
      },
      right: -300,
      zIndex: -1
    },
    subHeader: {
      borderBottom: "solid 1px #EAEAEA",
      margin: "30px",
      paddingBottom: 20
    },
    subHeaderDark: {
      borderBottom: "solid 1px #252728"
    },
    subHeaderTitle: {
      [theme.breakpoints.up("md")]: {
        paddingLeft: 0
      },
      display: "inline",
      paddingLeft: 10
    }
  });

export interface MenuNestedProps {
  activeItem: IActiveSubMenu;
  ariaLabel: string;
  closeSubMenu: ({ isActive, label }: IActiveSubMenu) => void;
  icon: string;
  menuItem: IMenuItem;
  title: string;
  handleSubMenu: (itemLabel: string) => void;
  onMenuItemClick: (url: string, event: React.MouseEvent<any>) => void;
}

const MenuNested = withStyles(styles, { name: "MenuNested" })(
  ({
    activeItem,
    ariaLabel,
    classes,
    closeSubMenu,
    icon,
    menuItem,
    onMenuItemClick,
    title
  }: MenuNestedProps & WithStyles<typeof styles>) => {
    const menuItems = menuItem.children;
    const { isDark } = useTheme();
    const closeMenu = (menuItemUrl, event) => {
      onMenuItemClick(menuItemUrl, event);
      closeSubMenu({
        isActive: false,
        label: null
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
                    label: null
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
                <Typography aria-label={item.ariaLabel}>
                  {item.label}
                </Typography>
              </a>
            );
          })}
        </div>
      </>
    );
  }
);
export default MenuNested;
