import Card from "material-ui/Card";
import Grid from "material-ui/Grid";
import { withStyles } from "material-ui/styles";
import * as React from "react";

const Page: React.StatelessComponent = ({ children }) => (
  <Grid item xs={12} md={9}>
    <Card>{children}</Card>
  </Grid>
);

export default Page;
