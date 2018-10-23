import Avatar from "@material-ui/core/Avatar";
import { withStyles } from "@material-ui/core/styles";
import TableCell from "@material-ui/core/TableCell";
import Cached from "@material-ui/icons/Cached";
import * as classNames from "classnames";
import * as React from "react";

import NoPhoto from "../../icons/NoPhoto";

interface TableCellAvatarProps {
  className?: string;
  thumbnail?: string;
  avatarProps?: string;
}

const decorate = withStyles(theme => ({
  avatar: {
    background: "none",
    border: "1px solid #eaeaea",
    borderRadius: 2,
    color: "#bdbdbd",
    padding: theme.spacing.unit / 2
  },
  root: {
    paddingLeft: theme.spacing.unit * 3,
    paddingRight: theme.spacing.unit * 3,
    width: "1%"
  }
}));
const TableCellAvatar = decorate<TableCellAvatarProps>(
  ({ classes, className, thumbnail, avatarProps }) => (
    <TableCell className={classNames(classes.root, className)}>
      {thumbnail === undefined ? (
        <Avatar className={classNames(classes.avatar, avatarProps)}>
          <Cached />
        </Avatar>
      ) : thumbnail === null ? (
        <Avatar className={classNames(classes.avatar, avatarProps)}>
          <NoPhoto />
        </Avatar>
      ) : (
        <Avatar
          className={classNames(classes.avatar, avatarProps)}
          src={thumbnail}
        />
      )}
    </TableCell>
  )
);
TableCellAvatar.displayName = "TableCellAvatar";
export default TableCellAvatar;
