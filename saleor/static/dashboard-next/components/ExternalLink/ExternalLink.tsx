import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Typography, { TypographyProps } from "@material-ui/core/Typography";
import * as React from "react";

const styles = createStyles({
  link: {
    textDecoration: "none"
  }
});

interface ExternalLinkProps
  extends React.HTMLProps<HTMLAnchorElement>,
    WithStyles<typeof styles> {
  href: string;
  className?: string;
  typographyProps?: TypographyProps;
}

const ExternalLink = withStyles(styles, { name: "ExternalLink" })(
  ({
    classes,
    className,
    children,
    href,
    typographyProps,
    ...props
  }: ExternalLinkProps) => (
    <a href={href} className={classes.link} {...props}>
      <Typography className={className} color="primary" {...typographyProps}>
        {children}
      </Typography>
    </a>
  )
);
ExternalLink.displayName = "ExternalLink";
export default ExternalLink;
