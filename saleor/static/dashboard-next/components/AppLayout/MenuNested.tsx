import Typography from "@material-ui/core/Typography";
import classNames from "classnames";
import * as React from "react";

import { User } from "../../auth/types/User";
import MenuList from "./MenuList";
import { IMenuItem } from "./menuStructure";

export interface MenuNestedProps {
  classes: Record<
    | "menuListItem"
    | "menuListItemActive"
    | "menuListItemText"
    | "menuListNested",
    string
  >;
  isAnyChildActive: boolean;
  menuItem: IMenuItem;
  location: string;
  user: User;
  onMenuItemClick: (url: string, event: React.MouseEvent<any>) => void;
}

const MenuNested: React.FC<MenuNestedProps> = ({
  classes,
  isAnyChildActive,
  location,
  menuItem,
  onMenuItemClick,
  user
}) => {
  const [isOpened, setOpenStatus] = React.useState(false);

  return (
    <div
      onClick={() => setOpenStatus(!isOpened)}
      className={classNames(classes.menuListItem, {
        [classes.menuListItemActive]: isAnyChildActive
      })}
    >
      <Typography
        aria-label={menuItem.ariaLabel}
        className={classes.menuListItemText}
      >
        {menuItem.label}
      </Typography>
      {isOpened && (
        <div className={classes.menuListNested}>
          <MenuList
            menuItems={menuItem.children}
            location={location}
            user={user}
            renderConfigure={false}
            onMenuItemClick={onMenuItemClick}
          />
        </div>
      )}
    </div>
  );
};
export default MenuNested;
