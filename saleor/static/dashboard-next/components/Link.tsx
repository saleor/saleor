import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

const styles = (theme: Theme) =>
  createStyles({
    primary: {
      color: theme.palette.primary.main
    },
    root: {
      cursor: "pointer",
      display: "inline"
    },
    secondary: {
      color: theme.palette.primary.main
    },
    underline: {
      textDecoration: "underline"
    }
  });

interface LinkProps
  extends React.AnchorHTMLAttributes<HTMLAnchorElement>,
    WithStyles<typeof styles> {
  color?: "primary" | "secondary";
  underline?: boolean;
  typographyProps?: TypographyProps;
}

const Link = withStyles(styles, { name: "Link" })(
  ({
    classes,
    className,
    children,
    color = "primary",
    underline = false,
    ...linkProps
  }: LinkProps) => (
    <Typography
      component="a"
      className={classNames({
        [classes.root]: true,
        [classes[color]]: true,
        [classes.underline]: underline
      })}
      {...linkProps}
    >
      {children}
    </Typography>
  )
);
Link.displayName = "Link";
export default Link;
