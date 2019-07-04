import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import classNames from "classnames";
import React from "react";

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
  onClick: () => void;
}

const Link = withStyles(styles, { name: "Link" })(
  ({
    classes,
    className,
    children,
    color = "primary",
    underline = false,
    onClick,
    ...linkProps
  }: LinkProps) => (
    <Typography
      component="a"
      className={classNames({
        [classes.root]: true,
        [classes[color]]: true,
        [classes.underline]: underline
      })}
      onClick={event => {
        event.preventDefault();
        onClick();
      }}
      {...linkProps}
    >
      {children}
    </Typography>
  )
);
Link.displayName = "Link";
export default Link;
