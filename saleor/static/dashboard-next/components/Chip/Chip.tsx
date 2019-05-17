import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import { fade } from "@material-ui/core/styles/colorManipulator";
import Typography from "@material-ui/core/Typography";
import CloseIcon from "@material-ui/icons/Close";
import classNames from "classnames";
import * as React from "react";

export interface ChipProps {
  className?: string;
  label: React.ReactNode;
  onClose?: () => void;
}

const styles = (theme: Theme) =>
  createStyles({
    closeIcon: {
      cursor: "pointer",
      fontSize: 16,
      marginLeft: theme.spacing.unit,
      verticalAlign: "middle"
    },
    label: {
      color: theme.palette.common.white
    },
    root: {
      background: fade(theme.palette.secondary.main, 0.6),
      borderRadius: 8,
      display: "inline-block",
      marginRight: theme.spacing.unit * 2,
      padding: "6px 12px"
    }
  });
const Chip = withStyles(styles, { name: "Chip" })(
  ({
    classes,
    className,
    label,
    onClose
  }: ChipProps & WithStyles<typeof styles>) => (
    <div className={classNames(classes.root, className)}>
      <Typography className={classes.label} variant="caption">
        {label}
        {onClose && (
          <CloseIcon className={classes.closeIcon} onClick={onClose} />
        )}
      </Typography>
    </div>
  )
);
Chip.displayName = "Chip";
export default Chip;
