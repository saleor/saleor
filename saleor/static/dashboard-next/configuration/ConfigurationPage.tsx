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
    disabled: boolean;
    icon: () => React.Component<IconProps>;
    title: string;
    url: string;
  }>;
  onSectionClick: (sectionName: string) => void;
}

const decorate = withStyles(theme => ({
  card: {
    "&:hover": {
      boxShadow: "0 12px 12px rgba(0, 0, 0, 0.1)"
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
    height: 48,
    width: 48
  },
  root: {
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
        {menu.map(menuItem => {
          const Icon = menuItem.icon;
          return (
            <Card
              className={
                menuItem.disabled ? classes.cardDisabled : classes.card
              }
            >
              <CardContent className={classes.cardContent}>
                <Icon className={classes.icon} />
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
          );
        })}
      </div>
    </Container>
  )
);
export default ConfigurationPage;
