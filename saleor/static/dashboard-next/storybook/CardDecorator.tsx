import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import * as React from "react";

const CardDecorator = storyFn => (
  <Card
    style={{
      margin: "auto",
      overflow: "visible",
      width: 400
    }}
  >
    <CardContent>{storyFn()}</CardContent>
  </Card>
);
export default CardDecorator;
