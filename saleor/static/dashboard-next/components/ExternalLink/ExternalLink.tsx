import { withStyles } from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as React from "react";

interface ExternalLinkProps extends React.HTMLProps<HTMLAnchorElement> {
  href: string,
  className?: string;
  typographyProps?: TypographyProps;
}

const decorate = withStyles({
  link: {
    textDecoration: "none",
  },
});
const ExternalLink = decorate<ExternalLinkProps>(
  ({ classes, className, children, href, typographyProps, ...props }) => (
    <>
      <a
        href={href}
        className={classes.link}
        {...props}
      >
        <Typography className={className} color="secondary" {...typographyProps}>{children}</Typography>
      </a>
    </>
  )
);
ExternalLink.displayName = "ExternalLink";
export default ExternalLink;
