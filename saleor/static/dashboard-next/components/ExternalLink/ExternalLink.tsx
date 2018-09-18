import { withStyles } from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import blue from "@material-ui/core/colors/blue";
import * as classNames from "classnames";
import * as React from "react";

interface ExternalLinkProps extends React.HTMLProps<HTMLAnchorElement> {
  href: string,
  className?: string;
  typographyProps?: TypographyProps;
}

const decorate = withStyles({
  link: {
    color: blue[500],
    cursor: "pointer",
    textDecoration: "none",
  },
});
const ExternalLink = decorate<ExternalLinkProps>(
  ({ classes, className, children, href, theme, typographyProps, ...props }) => (
    <>
      <a
        href={href}
        className={classNames(classes.link, className)}
        {...props}
      >
        <Typography {...typographyProps}>{children}</Typography>
      </a>
    </>
  )
);
ExternalLink.displayName = "ExternalLink";
export default ExternalLink;
