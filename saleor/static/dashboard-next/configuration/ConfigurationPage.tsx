import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import { withStyles } from "@material-ui/core/styles";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import { IconProps } from "@material-ui/core/Icon";
import Container from "../components/Container";
import PageHeader from "../components/PageHeader";
import i18n from "../i18n";

interface ConfigurationPageProps {
  menu: Array<{
    description: string;
    icon: React.ReactElement<IconProps>;
    title: string;
    url?: string;
  }>;
  onSectionClick: (sectionName: string) => void;
}

const decorate = withStyles(theme => ({
  card: {
    "&:hover": {
      boxShadow: theme.shadows[12]
    },
    cursor: "pointer" as "pointer",
    marginBottom: theme.spacing.unit * 3,
    transition: theme.transitions.duration.standard + "ms"
  },
  cardContent: {
    // Overrides Material-UI default theme
    "&:last-child": {
      paddingBottom: 16
    },
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 4 + "px",
    gridTemplateColumns: "48px 1fr"
  },
  cardDisabled: {
    "& $icon, & $sectionTitle, & $sectionDescription": {
      color: theme.palette.text.disabled
    },
    marginBottom: theme.spacing.unit * 3
  },
  icon: {
    color: theme.palette.primary.main,
    fontSize: 48
  },
  root: {
    [theme.breakpoints.down("md")]: {
      gridTemplateColumns: "1fr"
    },
    display: "grid" as "grid",
    gridColumnGap: theme.spacing.unit * 4 + "px",
    gridTemplateColumns: "1fr 1fr"
  },
  sectionDescription: {},
  sectionTitle: {
    fontWeight: 600 as 600,
    marginBottom: 4
  }
}));
export const ConfigurationPage = decorate<ConfigurationPageProps>(
  ({ classes, menu, onSectionClick }) => (
    <Container width="md">
      <PageHeader title={i18n.t("Configure")} />
      <div className={classes.root}>
        {menu.map((menuItem, menuItemIndex) => (
          <Card
            className={menuItem.url ? classes.card : classes.cardDisabled}
            onClick={() => onSectionClick(menuItem.url)}
            key={menuItemIndex}
          >
            <CardContent className={classes.cardContent}>
              <div className={classes.icon}>{menuItem.icon}</div>
              <div>
                <Typography className={classes.sectionTitle} color="primary">
                  {menuItem.title}
                </Typography>
                <Typography className={classes.sectionDescription}>
                  {menuItem.description}
                </Typography>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </Container>
  )
);
export default ConfigurationPage;
