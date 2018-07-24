import Avatar from "@material-ui/core/Avatar";
import { withStyles } from "@material-ui/core/styles";
import TableCell from "@material-ui/core/TableCell";
import Cached from "@material-ui/icons/Cached";
import * as React from "react";

import NoPhoto from "../../icons/NoPhoto";

interface TableCellAvatarProps {
  className?: string;
  thumbnail?: string;
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
    width: 5 * theme.spacing.unit
  }
}));
const TableCellAvatar = decorate<TableCellAvatarProps>(
  ({ classes, className, thumbnail }) => (
    <TableCell className={[classes.root, className].join(" ")}>
      {thumbnail === undefined ? (
        <Avatar className={classes.avatar}>
          <Cached />
        </Avatar>
      ) : thumbnail === null ? (
        <Avatar className={classes.avatar}>
          <NoPhoto />
        </Avatar>
      ) : (
        <Avatar className={classes.avatar} src={thumbnail} />
      )}
    </TableCell>
  )
);
TableCellAvatar.displayName = "TableCellAvatar";
export default TableCellAvatar;
