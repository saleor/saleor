import Card from "material-ui/Card";
import Grid from "material-ui/Grid";
import { withStyles } from "material-ui/styles";
import * as React from "react";

const Page: React.StatelessComponent = ({ children }) => (
  <Card>{children}</Card>
);

export default Page;
