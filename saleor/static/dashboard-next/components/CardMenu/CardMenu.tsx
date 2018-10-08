import IconButton from "@material-ui/core/IconButton";
import Menu from "@material-ui/core/Menu";
import MenuItem from "@material-ui/core/MenuItem";
import MoreVertIcon from "@material-ui/icons/MoreVert";
import * as React from "react";

const ITEM_HEIGHT = 48;

export interface CardMenuItem {
  label: string;
  onSelect: () => void;
}

export interface CardMenuProps {
  className?: string;
  menuItems: CardMenuItem[];
}
export interface CardMenuState {
  anchorEl: HTMLElement | null;
}

export class CardMenu extends React.Component<CardMenuProps, CardMenuState> {
  state = {
    anchorEl: null
  };

  handleClick = (event: React.MouseEvent<any>) => {
    this.setState({ anchorEl: event.currentTarget });
  };

  handleClose = () => {
    this.setState({ anchorEl: null });
  };

  handleMenuClick = (menuItemIndex: number) => {
    this.props.menuItems[menuItemIndex].onSelect();
    this.handleClose();
  };

  render() {
    const { anchorEl } = this.state;
    const open = !!anchorEl;

    return (
      <div className={this.props.className}>
        <IconButton
          aria-label="More"
          aria-owns={open ? "long-menu" : null}
          aria-haspopup="true"
          color="secondary"
          onClick={this.handleClick}
        >
          <MoreVertIcon />
        </IconButton>
        <Menu
          id="long-menu"
          anchorEl={anchorEl}
          open={open}
          onClose={this.handleClose}
          PaperProps={{
            style: {
              maxHeight: ITEM_HEIGHT * 4.5,
              width: 200
            }
          }}
        >
          {this.props.menuItems.map((menuItem, menuItemIndex) => (
            <MenuItem
              onClick={() => this.handleMenuClick(menuItemIndex)}
              key={menuItem.label}
            >
              {menuItem.label}
            </MenuItem>
          ))}
        </Menu>
      </div>
    );
  }
}

export default CardMenu;
