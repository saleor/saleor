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
  avatarSize?: string;
}

const decorate = withStyles(theme => ({
  root: {
    paddingLeft: theme.spacing.unit * 3,
    paddingRight: theme.spacing.unit * 3,
    width: "1%"
  }
}));
const TableCellAvatar = decorate<TableCellAvatarProps>(
  ({ classes, className, thumbnail, avatarSize }) => (
    <TableCell className={classNames(classes.root, className)}>
      {thumbnail === undefined ? (
        <Avatar className={classNames(avatarSize)}>
          <Cached />
        </Avatar>
      ) : thumbnail === null ? (
        <Avatar className={classNames(avatarSize)}>
          <NoPhoto />
        </Avatar>
      ) : (
        <Avatar className={classNames(avatarSize)} src={thumbnail} />
      )}
    </TableCell>
  )
);
TableCellAvatar.displayName = "TableCellAvatar";
export default TableCellAvatar;
