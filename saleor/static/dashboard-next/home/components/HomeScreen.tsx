import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import Typography from "@material-ui/core/Typography";
import * as React from "react";

import CardTitle from "../../components/CardTitle";
import Container from "../../components/Container";
import PageHeader from "../../components/PageHeader";
import i18n from "../../i18n";

interface HomeScreenProps {
  user: {
    email: string;
  };
}

export const HomeScreen: React.StatelessComponent<HomeScreenProps> = ({
  user
}) => (
  <Container>
    <PageHeader
      title={i18n.t("Hello there, {{userName}}", { userName: user.email })}
    />
    <Card>
      <CardTitle title={i18n.t("Disclaimer")} />
      <CardContent>
        <Typography>
          {i18n.t(
            "The new dashboard and the GraphQL API are preview-quality software."
          )}
        </Typography>
        <Typography>
          {i18n.t(
            "The GraphQL API is beta quality. It is not fully optimized and some mutations or queries may be missing."
          )}
        </Typography>
      </CardContent>
    </Card>
  </Container>
);
