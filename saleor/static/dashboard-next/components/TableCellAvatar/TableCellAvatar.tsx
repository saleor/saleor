import Avatar from "@material-ui/core/Avatar";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import TableCell from "@material-ui/core/TableCell";
import Cached from "@material-ui/icons/Cached";
import * as classNames from "classnames";
import * as React from "react";

import Image from "../../icons/Image";

const styles = (theme: Theme) =>
  createStyles({
    avatar: {
      background: "none",
      border: `1px solid ${theme.overrides.MuiCard.root.borderColor}`,
      borderRadius: 2,
      color: "#bdbdbd",
      padding: theme.spacing.unit / 2
    },
    root: {
      paddingRight: theme.spacing.unit * 3,
      width: "1%"
    }
  });

interface TableCellAvatarProps extends WithStyles<typeof styles> {
  className?: string;
  thumbnail?: string;
  avatarProps?: string;
}

const TableCellAvatar = withStyles(styles, { name: "TableCellAvatar" })(
  ({ classes, className, thumbnail, avatarProps }: TableCellAvatarProps) => (
    <TableCell className={classNames(classes.root, className)}>
      {thumbnail === undefined ? (
        <Avatar className={classNames(classes.avatar, avatarProps)}>
          <Cached color="primary" />
        </Avatar>
      ) : thumbnail === null ? (
        <Avatar className={classNames(classes.avatar, avatarProps)}>
          <Image color="primary" />
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
