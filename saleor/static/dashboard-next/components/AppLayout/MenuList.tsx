import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { appMountPoint } from "../..";
import { User } from "../../auth/types/User";
import { configurationMenu, configurationMenuUrl } from "../../configuration";
import i18n from "../../i18n";
import { removeDoubleSlashes } from "../../misc";
import Toggle from "../Toggle";
import { IMenuItem } from "./menuStructure";

const styles = (theme: Theme) =>
  createStyles({
    menuList: {
      display: "flex",
      flexDirection: "column",
      height: "100%",
      marginLeft: theme.spacing.unit * 4,
      marginTop: theme.spacing.unit * 2,
      paddingBottom: theme.spacing.unit * 3
    },
    menuListItem: {
      "&:hover": {
        color: theme.palette.primary.main
      },
      alignItems: "center",
      color: "#616161",
      display: "flex",
      marginTop: theme.spacing.unit * 2,
      paddingLeft: 0,
      textDecoration: "none",
      transition: theme.transitions.duration.standard + "ms"
    },
    menuListItemText: {
      "&:hover": {
        color: theme.palette.primary.main
      },
      cursor: "pointer",
      fontSize: "1rem",
      textTransform: "uppercase",
      transition: theme.transitions.duration.standard + "ms"
    },
    menuListNested: {
      marginLeft: theme.spacing.unit * 3
    }
  });

interface MenuListProps {
  className?: string;
  menuItems: IMenuItem[];
  user: User;
  onMenuItemClick: (url: string, event: React.MouseEvent<any>) => void;
}
const MenuList = withStyles(styles, { name: "MenuList" })(
  ({
    classes,
    className,
    menuItems,
    user,
    onMenuItemClick
  }: MenuListProps & WithStyles<typeof styles>) => (
    <div className={className}>
      {menuItems.map(menuItem => {
        if (
          menuItem.permission &&
          !user.permissions.map(perm => perm.code).includes(menuItem.permission)
        ) {
          return null;
        }
        if (!menuItem.url) {
          return (
            <Toggle key={menuItem.label}>
              {(openedMenu, { toggle: toggleMenu }) => (
                <>
                  <div onClick={toggleMenu} className={classes.menuListItem}>
                    <Typography
                      aria-label={menuItem.ariaLabel}
                      className={classes.menuListItemText}
                    >
                      {menuItem.label}
                    </Typography>
                  </div>
                  {openedMenu && (
                    <div className={classes.menuListNested}>
                      <MenuList
                        menuItems={menuItem.children}
                        user={user}
                        onMenuItemClick={onMenuItemClick}
                      />
                    </div>
                  )}
                </>
              )}
            </Toggle>
          );
        }
        return (
          <a
            className={classes.menuListItem}
            href={removeDoubleSlashes(appMountPoint + menuItem.url)}
            onClick={event => onMenuItemClick(menuItem.url, event)}
            key={menuItem.label}
          >
            <Typography
              aria-label={menuItem.ariaLabel}
              className={classes.menuListItemText}
            >
              {menuItem.label}
            </Typography>
          </a>
        );
      })}
      {configurationMenu.filter(menuItem =>
        user.permissions.map(perm => perm.code).includes(menuItem.permission)
      ).length > 0 && (
        <a
          className={classes.menuListItem}
          href={removeDoubleSlashes(appMountPoint + configurationMenuUrl)}
          onClick={event => onMenuItemClick(configurationMenuUrl, event)}
        >
          <Typography
            aria-label="configure"
            className={classes.menuListItemText}
          >
            {i18n.t("Configure")}
          </Typography>
        </a>
      )}
    </div>
  )
);
export default MenuList;
