import { withStyles } from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  color?: "primary" | "secondary";
  typographyProps?: TypographyProps;
}

const decorate = withStyles(theme => ({
  primary: {
    color: theme.palette.primary.main
  },
  root: {
    cursor: "pointer" as "pointer",
    textDecoration: "underline" as "underline"
  },
  secondary: {
    color: theme.palette.secondary.main
  }
}));
const Link = decorate<LinkProps>(
  ({ classes, className, children, color = "primary", ...linkProps }) => (
    <Typography
      component="a"
      className={classNames(classes.root, classes[color])}
      {...linkProps}
    >
      {children}
    </Typography>
  )
);
export default Link;
