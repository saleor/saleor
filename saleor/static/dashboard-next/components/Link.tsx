import { withStyles } from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  color?: "primary" | "secondary";
  underline?: boolean;
  typographyProps?: TypographyProps;
}

const decorate = withStyles(theme => ({
  primary: {
    color: theme.palette.primary.main
  },
  root: {
    cursor: "pointer" as "pointer",
    display: "inline" as "inline"
  },
  secondary: {
    color: theme.palette.secondary.main
  },
  underline: {
    textDecoration: "underline" as "underline"
  }
}));
const Link = decorate<LinkProps>(
  ({
    classes,
    className,
    children,
    color = "primary",
    underline = false,
    ...linkProps
  }) => (
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
