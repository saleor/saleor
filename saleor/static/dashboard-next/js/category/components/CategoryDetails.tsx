import Button from "material-ui/Button";
import Card, { CardActions, CardContent } from "material-ui/Card";
import Typography from "material-ui/Typography";
import * as React from "react";
import { Link } from "react-router-dom";

import { Skeleton } from "../../components/Skeleton";
import i18n from "../../i18n";

interface CategoryDetailsProps {
  description: string;
  editButtonLink: string;
  handleRemoveButtonClick?();
  loading: boolean;
  title: string;
}

export const CategoryDetails: React.StatelessComponent<
  CategoryDetailsProps
> = ({
  description,
  editButtonLink,
  handleRemoveButtonClick,
  loading,
  title
}) => (
  <Card>
    <CardContent>
      <Typography variant="headline" component="h2">
        {loading ? <Skeleton style={{ width: "10em" }} /> : title}
      </Typography>
      <Typography component="p">
        {loading
          ? [
              <Skeleton key="skel-1" style={{ width: "80%" }} />,
              <Skeleton key="skel-2" style={{ width: "75%" }} />,
              <Skeleton key="skel-3" style={{ width: "60%" }} />
            ]
          : description}
      </Typography>
    </CardContent>
    <CardActions>
      <Button
        color="primary"
        component={props => <Link to={editButtonLink} {...props} />}
      >
        {i18n.t("Edit", { context: "button" })}
      </Button>
      <Button color="primary" onClick={handleRemoveButtonClick}>
        {i18n.t("Delete", { context: "button" })}
      </Button>
    </CardActions>
  </Card>
);
